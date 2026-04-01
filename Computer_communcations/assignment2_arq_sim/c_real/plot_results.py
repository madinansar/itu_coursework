import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def main():
    try:
        df = pd.read_csv("simulation_results.csv")
    except FileNotFoundError:
        print("Error: simulation_results.csv not found. Run the C++ simulation first.")
        return

    print("Generating Heatmap...")
    
    # Pivot for Heatmap
    # Group by W and L, average Goodput over seeds
    heatmap_data = df.groupby(['W', 'L'])['Goodput_Mbps'].mean().unstack().sort_index(ascending=False)

    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="viridis", 
                cbar_kws={'label': 'Goodput (Mbps)'})
    
    plt.title("Simulated Goodput (Mbps) - Selective Repeat ARQ (C++ Optimized)")
    plt.xlabel("Frame Payload Size (L) [Bytes]")
    plt.ylabel("Window Size (W)")
    
    plt.savefig("goodput_heatmap.png")
    print("Heatmap saved to 'goodput_heatmap.png'")

if __name__ == "__main__":
    main()
