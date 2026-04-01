##### TO DO: Implement the encoder forward pass ############
##### TO DO: Implement the decoder forward pass ############
##### TO DO: Implement backpropagation for encoder and decoder ########
##### TO DO: Implement the full autoencoder forward function (call encoder + decoder) #######
##### TO DO: Compute the reconstruction loss (MSE) #########
##### TO DO: Update parameters using gradient descent ########

import numpy as np


class Autoencoder:
    def __init__(self, input_dim, hidden_dim, learning_rate=0.01):
        """
        Initialize weights and biases for a 1-layer encoder and 1-layer decoder.

        Parameters:
            input_dim  -- dimensionality of input (e.g., 784 for MNIST)
            hidden_dim -- dimensionality of bottleneck (e.g., 16, 32, or 64)
            learning_rate -- gradient descent step size
        """
        # Initialize weights with small random values
        self.W_e = np.random.randn(hidden_dim, input_dim) * 0.01
        self.b_e = np.zeros((hidden_dim, 1))
        self.W_d = np.random.randn(input_dim, hidden_dim) * 0.01
        self.b_d = np.zeros((input_dim, 1))

        self.lr = learning_rate

    def sigmoid(self, x):   # sigmoid activation function
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def deriv_sigmoid(self, x):
        sig = self.sigmoid(x)
        return sig * (1 - sig)

    def encoder(self, x):   # x -> z
        z = np.dot(self.W_e, x) + self.b_e
        z = self.sigmoid(z)
        return z

    def decoder(self, z):   # z -> x_hat
        x_hat = np.dot(self.W_d, z) + self.b_d
        x_hat = self.sigmoid(x_hat)
        return x_hat


    def compute_loss(self, x, x_hat):   #MSE
        loss = np.mean((x - x_hat) ** 2)
        return loss


    def backward(self, x, z, x_hat):    # get gradients using backpropagation
        m = x.shape[1]  # batch size, for mean error

        #gradient for MSE
        dL_dx_hat = 2.0 / m * (x_hat - x)

        # Backward through decoder sigmoid
        # z_d is the input to decoder sigmoid (before activation)
        z_d = np.dot(self.W_d, z) + self.b_d
        dL_dz_d = dL_dx_hat * self.deriv_sigmoid(z_d)
        
        #gradients for decoder params
        dW_d = np.dot(dL_dz_d, z.T)
        db_d = np.sum(dL_dz_d, axis=1, keepdims=True)

        # Backward through W_d to get gradient wrt z
        dL_dz = np.dot(self.W_d.T, dL_dz_d)

        # Backward through encoder sigmoid
        # z_e is the input to encoder sigmoid (before activation)
        z_e = np.dot(self.W_e, x) + self.b_e
        dL_dz_e = dL_dz * self.deriv_sigmoid(z_e)
        
        #gradients for encoder params
        dW_e = np.dot(dL_dz_e, x.T)
        db_e = np.sum(dL_dz_e, axis=1, keepdims=True)

        grads = {
            'W_e': dW_e,
            'b_e': db_e,
            'W_d': dW_d,
            'b_d': db_d
        }
        return grads
    

    def step(self, grads):  # upd params using gradient decent: w = w - lr*grad
        self.W_e -= self.lr * grads['W_e']
        self.b_e -= self.lr * grads['b_e']
        self.W_d -= self.lr * grads['W_d']
        self.b_d -= self.lr * grads['b_d']

        
    def train(self, X, epochs=20, batch_size=128):
        n_samples = X.shape[0]
        losses = []

        for epoch in range(epochs):
            # shuffled data
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            
            epoch_losses = []

            #batch training
            for i in range(0, n_samples, batch_size):
                #get batch
                X_batch = X_shuffled[i:i+batch_size]

                # Transpose to shape (input_dim, batch_size)
                X_batch = X_batch.T
                
                #forward pass
                z = self.encoder(X_batch)
                x_hat = self.decoder(z)
                
                #compute loss
                loss = self.compute_loss(X_batch, x_hat)
                epoch_losses.append(loss)
                
                #backward pass
                grads = self.backward(X_batch, z, x_hat)
                
                #update parameters
                self.step(grads)
            
            # Record average loss for this epoch
            avg_loss = np.mean(epoch_losses)
            losses.append(avg_loss)
            
            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
        
        return losses




