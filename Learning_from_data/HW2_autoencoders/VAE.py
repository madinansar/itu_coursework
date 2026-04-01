# VAE.py
# Template for implementing a Variational Autoencoder (VAE) in PyTorch

##### TO DO: Implement the encoder network to output mean and log-variance #####
##### TO DO: Implement the reparameterization trick to sample latent vectors #####
##### TO DO: Implement the decoder network to reconstruct images from latent vectors #####
##### TO DO: Implement the full forward pass (encoder -> reparameterization -> decoder) #####
##### TO DO: Compute the reconstruction loss (e.g., MSE or BCE) #####
##### TO DO: Compute the KL divergence loss for the latent distribution #####
##### TO DO: Combine reconstruction + KL loss to form the total loss #####
##### TO DO: Update model parameters using an optimizer (e.g., Adam) #####



import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class VAE(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=400, latent_dim=20):
        """
        Initialize the VAE model.

        Parameters:
        - input_dim: dimensionality of input (e.g., 784 for MNIST)
        - hidden_dim: number of units in the hidden layer
        - latent_dim: dimensionality of the latent space
        """
        super(VAE, self).__init__()

        # ===== TO DO: Define encoder layers =====
        # Example:
        # self.fc1 = nn.Linear(input_dim, hidden_dim)
        # self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        # self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        # =======================================
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        # ===== TO DO: Define decoder layers =====
        # Example:
        # self.fc2 = nn.Linear(latent_dim, hidden_dim)
        # self.fc3 = nn.Linear(hidden_dim, input_dim)
        # =======================================
        self.fc2 = nn.Linear(latent_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, input_dim)

    def encode(self, x):
        """
        Encode input x into latent mean and log-variance.

        Input:
        - x: tensor of shape (batch_size, input_dim)

        Returns:
        - mu: mean of latent distribution
        - logvar: log-variance of latent distribution
        """
        h = F.relu(self.fc1(x))
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu, logvar):
        """
        Apply the reparameterization trick to sample z ~ N(mu, sigma^2).

        Input:
        - mu: mean tensor
        - logvar: log-variance tensor

        Returns:
        - z: sampled latent vector
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mu + eps * std
        return z

    def decode(self, z):
        """
        Decode latent vector z to reconstruct input x_hat.

        Input:
        - z: latent vector tensor

        Returns:
        - x_hat: reconstructed input
        """
        h = F.relu(self.fc2(z))
        x_hat = torch.sigmoid(self.fc3(h))
        return x_hat

    def forward(self, x):
        """
        Forward pass: encode -> reparameterize -> decode.

        Input:
        - x: input tensor

        Returns:
        - x_hat: reconstructed input
        - mu: latent mean
        - logvar: latent log-variance
        """
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        x_hat = self.decode(z)
        return x_hat, mu, logvar
    
     
    def train_vae(self, X, epochs=20, batch_size=128, learning_rate=0.01, device = 'cpu'):
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X).float()

        self.to(device)
        X = X.to(device)

        optimizer = optim.Adam(self.parameters(), lr=learning_rate)
        
        n_samples = X.shape[0]
        history = []

        for epoch in range(epochs):
            self.train()

            # 1. Shuffle data
            indices = torch.randperm(n_samples)
            X_shuffled = X[indices]

            epoch_loss = 0

            for i in range(0, n_samples, batch_size):
                # Slice the batch manually
                x_batch = X_shuffled[i:i+batch_size]

                optimizer.zero_grad()           # clear old gradients
                x_hat, mu, logvar = self(x_batch) # Forward pass
                loss = vae_loss(x_batch, x_hat, mu, logvar) # Calculate loss
                loss.backward()                 # Calculate gradients
                optimizer.step()                # Update weights (Adam)

                epoch_loss += loss.item()

            # Calculate average for the epoch (sum of batch averages / num batches)
            num_batches = (n_samples + batch_size - 1) // batch_size
            # Average per Sample
            avg_loss = epoch_loss / n_samples
            history.append(avg_loss)
            
            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
                
        return history


def vae_loss(x, x_hat, mu, logvar):
    """
    Compute the VAE loss (ELBO) = reconstruction loss + KL divergence.

    Inputs:
    - x: original input
    - x_hat: reconstructed input
    - mu: latent mean
    - logvar: latent log-variance

    Returns:
    - loss: scalar tensor
    """
    # Reconstruction loss (Binary Cross Entropy)
    recon_loss = F.binary_cross_entropy(x_hat, x, reduction='sum')

    # KL Divergence loss
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    
    # Total loss
    loss = recon_loss + kl_loss
    
    return loss
       