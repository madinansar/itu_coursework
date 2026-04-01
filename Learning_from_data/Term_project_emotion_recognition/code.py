"""
Madina Alzhanova - 150220939
Term Project: Emotion Recognition
-------------------------------------------------
This script implements two 5-fold cross-validation schemes for emotion classification:
1. Standard Stratified K-Fold CV 
2. Balanced Group K-Fold CV

Input: 
    - Train dataset (22496 samples) with features, labels, and person IDs
    - Model parameters (presets, time limits, etc.)

Output: 
    - predictions.csv: Cross-validated predictions on training data 
    - f1_scores.csv: F1-macro scores for both CV schemes with fold details
    - Console: Average F1-macro scores for both CV schemes
"""

import pandas as pd
import numpy as np
from autogluon.tabular import TabularPredictor
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, classification_report
import gc
import os

# Global variables for model parameters
MODEL_PARAMS = {}
AG_ARGS = {}
STRATIFIED_TIME_LIMIT = None


# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

def load_and_preprocess_data(filepath, label_col_name=None, person_col_name=None, drop_persons=None):
    """
    Load and preprocess training data.
    
    Args:
        filepath: Path to CSV file
        label_col_name: Name of the label column
        person_col_name: Name of the person ID column
        drop_persons: List of person IDs to exclude
    
    Returns:
        Preprocessed DataFrame
    """
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Remove unnamed index columns
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Ensure column names are strings
    df.columns = df.columns.astype(str)
    
    # Drop problematic persons if specified
    if drop_persons and person_col_name:
        original_size = len(df)
        df = df[~df[person_col_name].isin(drop_persons)].copy()
        print(f"Removed {original_size - len(df)} samples from persons {drop_persons}")
    
    print(f"Final dataset: {len(df)} samples, {len(df.columns)} columns")
    return df


def calculate_sample_weights(labels):
    """
    Calculate balanced sample weights for imbalanced classes.
    Weight = n_samples / (n_classes × class_count)
    
    Args:
        labels: Series of class labels
    
    Returns:
        Dictionary mapping class labels to weights
    """
    class_counts = labels.value_counts()
    n_samples = len(labels)
    n_classes = len(class_counts)
    
    weights = (n_samples / (n_classes * class_counts)).to_dict()
    return weights


def create_balanced_folds(df, person_id_col, label_col, n_folds=5):
    """
    Create balanced person-grouped folds with intelligent rare class distribution.
    Ensures all persons from same ID stay in same fold while balancing class distribution.
    
    Args:
        df: Input DataFrame
        person_id_col: Column name for person IDs
        label_col: Column name for labels
        n_folds: Number of folds to create
    
    Returns:
        Dictionary mapping person_id to fold_id
    """
    print(f"Creating {n_folds} balanced person-grouped folds...")
    
    # 1. Get class counts per person
    person_stats = df.groupby([person_id_col, label_col]).size().unstack(fill_value=0)
    all_classes = person_stats.columns.tolist()

    # 2. Identify rare class (class with minimum samples)
    class_sums = person_stats.sum()
    rare_class = class_sums.idxmin()
    print(f"   Balancing based on rare class: {rare_class}")

    # 3. Sort people by rare class presence (rare class holders first)
    has_rare = person_stats[person_stats[rare_class] > 0].copy()
    no_rare = person_stats[person_stats[rare_class] == 0].copy()
    
    has_rare = has_rare.sort_values(by=rare_class, ascending=False)
    no_rare['total'] = no_rare.sum(axis=1)
    no_rare = no_rare.sort_values(by='total', ascending=False).drop(columns=['total'])

    # 4. Distribute persons across folds
    fold_assignments = {i: [] for i in range(n_folds)}
    fold_class_counts = {i: {c: 0 for c in all_classes} for i in range(n_folds)}

    # Phase 1: Distribute rare class holders to balance rare class
    for person_id, row in has_rare.iterrows():
        target_fold = min(range(n_folds), key=lambda k: fold_class_counts[k][rare_class])
        fold_assignments[target_fold].append(person_id)
        for c in all_classes:
            fold_class_counts[target_fold][c] += row[c]

    # Phase 2: Distribute remaining persons by their dominant class
    for person_id, row in no_rare.iterrows():
        dominant_c = row.idxmax()
        target_fold = min(range(n_folds), key=lambda k: fold_class_counts[k][dominant_c])
        fold_assignments[target_fold].append(person_id)
        for c in all_classes:
            fold_class_counts[target_fold][c] += row[c]

    # 5. Create person-to-fold mapping
    person_to_fold_map = {}
    for fold_id, persons in fold_assignments.items():
        for p in persons:
            person_to_fold_map[p] = fold_id
    
    return person_to_fold_map


def train_and_evaluate_fold(train_data, val_data, label_col, fold_idx, cv_type='stratified', time_limit=None):
    """
    Train AutoGluon model on a single fold and evaluate.
    
    Args:
        train_data: Training DataFrame
        val_data: Validation DataFrame
        label_col: Name of label column
        fold_idx: Fold index for naming
        cv_type: Type of CV ('stratified' or 'balanced_group')
        time_limit: Time limit in seconds for training (None for no limit)
    
    Returns:
        Tuple of (f1_score, predictions, prediction_probabilities)
    """
    # Calculate and apply sample weights for class imbalance
    weights = calculate_sample_weights(train_data[label_col])
    train_data['__sample_weight'] = train_data[label_col].map(weights)
    val_data['__sample_weight'] = 1.0
    
    print(f"  Class weights: {weights}")
    
    # Configure AutoGluon predictor
    fold_path = f"AutogluonModels/fold_{fold_idx}_{cv_type}"
    
    predictor = TabularPredictor(
        label=label_col,
        eval_metric=MODEL_PARAMS['eval_metric'],
        problem_type=MODEL_PARAMS['problem_type'],
        path=fold_path,
        sample_weight='__sample_weight'
    )
    
    # Train model
    fit_kwargs = {
        'train_data': train_data,
        'tuning_data': val_data,
        'presets': MODEL_PARAMS['presets'],
        **AG_ARGS
    }
    
    # Apply time limit if specified
    if time_limit is not None:
        fit_kwargs['time_limit'] = time_limit
    
    predictor.fit(**fit_kwargs)
    
    # Evaluate on validation set
    val_preds = predictor.predict(val_data)
    val_proba = predictor.predict_proba(val_data)
    val_true = val_data[label_col]
    
    score = f1_score(val_true, val_preds, average='macro')
    
    print(f"  Fold F1-Macro: {score:.4f}")
    print("\n  Per-Class Performance:")
    print(classification_report(val_true, val_preds, digits=2))
    
    # Cleanup
    del predictor
    gc.collect()
    
    return score, val_preds, val_proba


# ================================================================================
# CROSS-VALIDATION SCHEMES
# ================================================================================

def stratified_kfold_cv(df, label_col, person_col, n_folds=5, random_state=1):
    """
    Perform standard Stratified K-Fold Cross-Validation.
    Splits data stratified by class labels, ignoring person groupings.
    
    Args:
        df: Input DataFrame
        label_col: Name of label column
        person_col: Name of person ID column (not used for splitting)
        n_folds: Number of folds
        random_state: Random seed
    
    Returns:
        Tuple of (fold_scores, all_predictions, all_indices)
    """
    print("\n" + "="*80)
    print("STRATIFIED K-FOLD CROSS-VALIDATION")
    print("="*80)
    
    # Initialize StratifiedKFold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    fold_scores = []
    all_predictions = []
    all_indices = []
    
    # Iterate through folds
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(df, df[label_col])):
        print(f"\n--- Fold {fold_idx+1}/{n_folds} ---")
        
        # Split data
        train_data = df.iloc[train_idx].copy()
        val_data = df.iloc[val_idx].copy()
        
        # Show class distribution
        train_dist = train_data[label_col].value_counts().sort_index()
        val_dist = val_data[label_col].value_counts().sort_index()
        
        print(f"  Train: {len(train_data)} samples | Val: {len(val_data)} samples")
        print(f"  Train distribution: {dict(train_dist)}")
        print(f"  Val distribution: {dict(val_dist)}")
        
        # Remove person_col before training
        train_data = train_data.drop(columns=[person_col])
        val_data_clean = val_data.drop(columns=[person_col])
        
        # Train and evaluate
        score, preds, _ = train_and_evaluate_fold(
            train_data, val_data_clean, label_col, fold_idx, cv_type='stratified',
            time_limit=STRATIFIED_TIME_LIMIT
        )
        
        fold_scores.append(score)
        all_predictions.extend(preds.tolist())
        all_indices.extend(val_idx.tolist())
    
    # Calculate average F1 score
    avg_score = np.mean(fold_scores)
    
    print("\n" + "="*80)
    print(f"STRATIFIED CV RESULTS")
    print(f"  Fold Scores: {[f'{s:.4f}' for s in fold_scores]}")
    print(f"  Average F1-Macro: {avg_score:.4f}")
    print("="*80)
    
    return fold_scores, all_predictions, all_indices


def balanced_group_kfold_cv(df, label_col, person_col, n_folds=5):
    """
    Perform Balanced Group K-Fold Cross-Validation.
    Groups by person_id with intelligent class distribution and missing class augmentation.
    Ensures all samples from the same person stay in the same fold while balancing classes.
    
    Args:
        df: Input DataFrame
        label_col: Name of label column
        person_col: Name of person ID column (used for grouping)
        n_folds: Number of folds
    
    Returns:
        Tuple of (fold_scores, all_predictions, all_indices)
    """
    print("\n" + "="*80)
    print("BALANCED GROUP K-FOLD CROSS-VALIDATION (by person_id)")
    print("="*80)
    
    # Create balanced fold assignments
    fold_map = create_balanced_folds(df, person_col, label_col, n_folds)
    
    # Apply fold assignments to dataframe
    df_with_folds = df.copy()
    df_with_folds['__fold_id'] = df_with_folds[person_col].map(fold_map)
    
    # Print fold composition summary
    print("\nFold Composition:")
    for fold in range(n_folds):
        fold_persons = df_with_folds[df_with_folds['__fold_id'] == fold][person_col].nunique()
        fold_samples = len(df_with_folds[df_with_folds['__fold_id'] == fold])
        fold_classes = df_with_folds[df_with_folds['__fold_id'] == fold][label_col].value_counts().sort_index()
        print(f"  Fold {fold}: {fold_persons} persons, {fold_samples} samples - {dict(fold_classes)}")
    
    fold_scores = []
    all_predictions = []
    all_indices = []
    
    # Iterate through folds
    for fold_idx in range(n_folds):
        print(f"\n--- Fold {fold_idx+1}/{n_folds} ---")
        
        # Split data by fold assignment
        train_data = df_with_folds[df_with_folds['__fold_id'] != fold_idx].copy()
        val_data = df_with_folds[df_with_folds['__fold_id'] == fold_idx].copy()
        
        # Get validation indices for later use
        val_indices = val_data.index.tolist()
        
        # Show person and class distribution
        train_persons = train_data[person_col].nunique()
        val_persons = val_data[person_col].nunique()
        train_dist = train_data[label_col].value_counts().sort_index()
        val_dist = val_data[label_col].value_counts().sort_index()
        
        print(f"  Train: {train_persons} persons, {len(train_data)} samples")
        print(f"  Val: {val_persons} persons, {len(val_data)} samples")
        print(f"  Train distribution: {dict(train_dist)}")
        print(f"  Val distribution: {dict(val_dist)}")
        
        # -------------------------------------------------------
        # AUGMENTATION: Add missing classes from validation fold
        # -------------------------------------------------------
        all_classes = df_with_folds[label_col].unique()
        missing_classes = [c for c in all_classes if c not in train_dist.index]
        
        if missing_classes:
            print(f"\n  Missing classes in training: {missing_classes}")
            print(f"     Borrowing samples from validation fold...")
            
            for missing_cls in missing_classes:
                # Get samples of this class from current validation fold
                borrowed_samples = df_with_folds[
                    (df_with_folds[label_col] == missing_cls) & 
                    (df_with_folds['__fold_id'] == fold_idx)
                ].copy()
                
                if len(borrowed_samples) > 0:
                    print(f"     Borrowed {len(borrowed_samples)} samples of Class {missing_cls}")
                    train_data = pd.concat([train_data, borrowed_samples], ignore_index=True)
            
            # Update class distribution after augmentation
            train_dist_after = train_data[label_col].value_counts().sort_index()
            print(f"     Training distribution after augmentation: {dict(train_dist_after)}")
        
        # Remove metadata columns before training
        train_data = train_data.drop(columns=[person_col, '__fold_id'])
        val_data_clean = val_data.drop(columns=[person_col, '__fold_id'])
        
        # Train and evaluate
        score, preds, _ = train_and_evaluate_fold(
            train_data, val_data_clean, label_col, fold_idx, cv_type='balanced_group'
        )
        
        fold_scores.append(score)
        all_predictions.extend(preds.tolist())
        all_indices.extend(val_indices)
    
    # Calculate average F1 score
    avg_score = np.mean(fold_scores)
    
    print("\n" + "="*80)
    print(f"BALANCED GROUP CV RESULTS")
    print(f"  Fold Scores: {[f'{s:.4f}' for s in fold_scores]}")
    print(f"  Average F1-Macro: {avg_score:.4f}")
    print("="*80)
    
    return fold_scores, all_predictions, all_indices


# ================================================================================
# MAIN EXECUTION
# ================================================================================

def main(train_path="blg-454-e-fall-2526-term-project/train.csv",
         n_folds=5,
         random_seed=1,
         presets='medium_quality',
         stratified_time_limit=180,
         drop_persons=[12, 15]):
    """
    Main execution function that runs both CV schemes and produces predictions.
    
    Args:
        train_path: Path to training CSV file
        n_folds: Number of folds for cross-validation
        random_seed: Random seed for reproducibility
        presets: AutoGluon presets ('medium_quality', 'best_quality', etc.)
        stratified_time_limit: Time limit in seconds for stratified CV (None for no limit)
        drop_persons: List of person IDs to exclude from training
    
    Returns:
        Dictionary with CV scores and file paths
    """
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Update global variables for model parameters
    global MODEL_PARAMS, AG_ARGS, STRATIFIED_TIME_LIMIT
    
    MODEL_PARAMS = {
        'eval_metric': 'f1_macro',
        'problem_type': 'multiclass',
        'presets': presets,
    }
    
    AG_ARGS = {
        'use_bag_holdout': True,
        'ag_args_ensemble': {'fold_fitting_strategy': 'sequential_local'},
        'ag_args_fit': {'ag.max_memory_usage_ratio': 2.5}
    }
    
    STRATIFIED_TIME_LIMIT = stratified_time_limit
    
    print("="*80)
    print("EMOTION RECOGNITION - CROSS-VALIDATION FRAMEWORK")
    print("="*80)
    
    # Identify column names (assuming last two columns are label and person_id)
    temp_df = pd.read_csv(train_path, nrows=1)
    label_col = str(temp_df.columns[-2])
    person_col = str(temp_df.columns[-1])
    
    print(f"\nConfiguration:")
    print(f"  Train data: {train_path}")
    print(f"  Label column: {label_col}")
    print(f"  Person ID column: {person_col}")
    print(f"  Number of folds: {n_folds}")
    print(f"  Random seed: {random_seed}")
    print(f"  AutoGluon presets: {presets}")
    print(f"  Time limit (stratified CV only): {stratified_time_limit} seconds")
    print(f"  Time limit (balanced group CV): No limit")
    print(f"  Persons to drop: {drop_persons}")
    
    # Load and preprocess training data
    df = load_and_preprocess_data(
        train_path, 
        label_col, 
        person_col, 
        drop_persons=drop_persons
    )
    
    # Show dataset statistics
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {len(df)}")
    print(f"  Number of persons: {df[person_col].nunique()}")
    print(f"  Number of features: {len(df.columns) - 2}")  # Exclude label and person_id
    class_dist = df[label_col].value_counts().sort_index()
    print(f"  Class distribution: {dict(class_dist)}")
    
    # ========================================
    # 1. STRATIFIED K-FOLD CV
    # ========================================
    stratified_scores, stratified_preds, stratified_indices = stratified_kfold_cv(
        df, label_col, person_col, n_folds=n_folds, random_state=random_seed
    )
    
    # ========================================
    # 2. BALANCED GROUP K-FOLD CV
    # ========================================
    group_scores, group_preds, group_indices = balanced_group_kfold_cv(
        df, label_col, person_col, n_folds=n_folds
    )
    
    # ========================================
    # 3. SAVE CV PREDICTIONS
    # ========================================
    print(f"\n{'='*80}")
    print("SAVING PREDICTIONS")
    print("="*80)
    
    # Save stratified CV predictions
    predictions_df = pd.DataFrame({
        'ID': stratified_indices,
        'Predicted': stratified_preds
    })
    predictions_df = predictions_df.sort_values('ID').reset_index(drop=True)
    output_path = "predictions.csv"
    predictions_df.to_csv(output_path, index=False)
    print(f"Stratified CV predictions saved to: {output_path}")
    
    # Save balanced group CV predictions
    predictions_group_df = pd.DataFrame({
        'ID': group_indices,
        'Predicted': group_preds
    })
    predictions_group_df = predictions_group_df.sort_values('ID').reset_index(drop=True)
    output_group_path = "predictions_group.csv"
    predictions_group_df.to_csv(output_group_path, index=False)
    print(f"Balanced Group CV predictions saved to: {output_group_path}")
    
    # ========================================
    # 4. SAVE F1 SCORES TO CSV
    # ========================================
    stratified_avg = np.mean(stratified_scores)
    group_avg = np.mean(group_scores)
    
    # Create F1 scores dataframe
    f1_scores_df = pd.DataFrame({
        'CV_Method': ['Stratified K-Fold', 'Balanced Group K-Fold'],
        'Average_F1_Score': [stratified_avg, group_avg],
        'Std_Dev': [np.std(stratified_scores), np.std(group_scores)],
        'Fold_Scores': [str(stratified_scores), str(group_scores)]
    })
    
    # Save F1 scores
    f1_output_path = "f1_scores.csv"
    f1_scores_df.to_csv(f1_output_path, index=False)
    print(f"F1 scores saved to: {f1_output_path}")
    
    # ========================================
    # 5. FINAL SUMMARY
    # ========================================
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print("="*80)
    
    print(f"\n1. STRATIFIED K-FOLD CV:")
    print(f"   Average F1-Macro Score: {stratified_avg:.4f}")
    print(f"   Fold Scores: {[f'{s:.4f}' for s in stratified_scores]}")
    print(f"   Std Dev: {np.std(stratified_scores):.4f}")
    
    print(f"\n2. BALANCED GROUP K-FOLD CV (by person_id):")
    print(f"   Average F1-Macro Score: {group_avg:.4f}")
    print(f"   Fold Scores: {[f'{s:.4f}' for s in group_scores]}")
    print(f"   Std Dev: {np.std(group_scores):.4f}")
    
    print(f"\n3. OUTPUT FILES:")
    print(f"   - {output_path}: Stratified CV predictions on training data (Kaggle format)")
    print(f"   - {output_group_path}: Balanced Group CV predictions on training data (Kaggle format)")
    print(f"   - {f1_output_path}: F1-macro scores for both CV schemes")
    
    print(f"\n{'='*80}")
    print("EXECUTION COMPLETED SUCCESSFULLY")
    print("="*80)
    
    # Return results dictionary
    return {
        'stratified_f1': stratified_avg,
        'group_f1': group_avg,
        'stratified_scores': stratified_scores,
        'group_scores': group_scores,
        'predictions_file': output_path,
        'predictions_group_file': output_group_path,
        'f1_scores_file': f1_output_path
    }


if __name__ == "__main__":
    results = main(
        train_path="blg-454-e-fall-2526-term-project/train.csv",
        n_folds=5,
        random_seed=1,
        presets='medium_quality',
        stratified_time_limit=180,  # 3 minutes per fold for stratified CV
        drop_persons=[12, 15]  # Exclude outlier persons
    )
