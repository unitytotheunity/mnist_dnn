# Dillon Notz, 2018
# Purpose: Construct, train, and test N-layer deep NN on MNIST handwritten number
# dataset.
# NN Architecture: LINEAR -> RELU -> LINEAR -> RELU -> LINEAR -> SOFTMAX

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from time import process_time

# TODO: make larger dataset visualization function

# Visualizes a few training examples to ensure correct construction
def visualize_dataset():
	None

def draw_image(arr, label_num):
	# Use matplotlib to save example as an image
	img = arr.reshape((28,28))
	plt.imshow(img)
	plt.draw()
	plt.savefig('input_image')
	print("Image label = ",int(label_num))

# Imports Kaggle's MNIST handwritten digit dataset files to numpy arrays,
# then stores these as clean numpy ".npy" binaries for easier handling
# in TensorFlow.
def import_dataset():
	# Load data from dataset ("train" is labeled, "test" is unlabelled)
	train = np.genfromtxt('../data/csv/train.csv', delimiter=',', skip_header=1)
	test  = np.genfromtxt( '../data/csv/test.csv', delimiter=',', skip_header=1)

	# Save files to /digit_recognition/data for efficiently loading into main Tensorflow project
	np.save('../train.npy', train)
	np.save( '../test.npy',  test)

# Loads 'X_train.npy' and 'Y_train.npy' to produce training and dev sets
def load_dataset(split_ratio=0.8):
	# Load data from file
	data = np.load('../data/train.npy')

	# Randomly shuffle examples to obtain uniform distribution
	m = data.shape[0]       # Total number of examples in data set
	np.random.shuffle(data)

	# Separate data labels from examples
	X_data = data[:,1:]
	Y_data = data[:,0].reshape((m,1))

	# Split dataset into training set (80%) and development set (20%)
	m_t = int(np.ceil(m * split_ratio)); print('Number of examples in training set: ', m_t)
	m_d = m - m_t; print('Number of examples in development set: ', m_d)

	X_train = X_data[:m_t,:].T
	Y_train = Y_data[:m_t]
	X_dev   = X_data[m_t:,:].T
	Y_dev   = Y_data[m_t:]

	return X_train, X_dev, Y_train, Y_dev

def load_eval_dataset():
	'''
	Load unlabeled dataset to produce predictions for online Kaggle MNIST submission
	'''
	X_eval = np.load('../data/test.npy')

	return X_eval

def compute_matrix_dims(layer_sizes):
	'''
	Computes matrix dimensions for each layer

	Arguments:
	layer_sizes - List containing numbers of neurons in each layer

	Asserts:
	n_layers > 1 - Ensures model has at least 1 hidden layer

	Returns:
	nn_dims - Dictionary containing tuples of matrix shapes for each layer's weights
		and biases

	'''
	nn_dims = {}
	n_layers = len(layer_sizes)-1 # Input features don't count as a layer

	# Ensure the presence of at least 1 hidden layer
	assert n_layers >= 1

	# Build nn_dims list holding matrix sizes
	for i in range(0,n_layers):
		layer_prev = layer_sizes[i]
		layer_curr = layer_sizes[i+1]
		nn_dims["W"+str(i+1)] = (layer_curr,layer_prev)
		nn_dims['b'+str(i+1)] = (layer_curr,1)

		#print("W" + str(i+1) + " = " + str(nn_dims['W'+str(i+1)]) + ", "
		#	+ "b" + str(i+1) + " = " + str(nn_dims['b'+str(i+1)]))

	return nn_dims

def create_placeholders(n_x, n_y):
	'''
	Creates the placeholders for the tensorflow session.
    
    Arguments:
    n_x - scalar, size of an image vector (num_px * num_px = 64 * 64 * 3 = 12288)
    n_y - scalar, number of classes (from 0 to 5, so -> 6)
    
    Returns:
    X - placeholder for the data input, of shape [n_x, None] and dtype "float"
    Y - placeholder for the input labels, of shape [n_y, None] and dtype "float"
	'''

	X = tf.placeholder(dtype=tf.float32, shape=(n_x, None), name='X')
	Y = tf.placeholder(dtype=tf.float32, shape=(n_y, None), name='Y')

	return X, Y
	

def initialize_parameters(nn_dims):
	'''
	Initializes weights randomly with Xavier initialization and biases with zeros.

	Arguments:
	nn_dims - Dictionary that holds the shapes of each layer's weight/bias tensors.

	Returns:
	parameters - Dictionary holding weights and bias tensors for Tensorflow graph 
	'''

	parameters = {}

	for i in range(1,len(nn_dims)//2 + 1):
		w = 'W'+str(i); b = 'b'+str(i)
		parameters[w] = tf.get_variable(w, nn_dims[w], initializer=tf.contrib.layers.xavier_initializer(seed = 1))
		parameters[b] = tf.get_variable(b, nn_dims[b], initializer=tf.zeros_initializer())

	return parameters

def convert_to_one_hot(labels, num_classes=10):
	'''
	Creates a matrix where the i-th row corresponds to the i-th class number and the j-th column
	    corresponds to the j-th training example. i.e. If example j has label i, entry (i,j) 
	    will be 1 with zeros in all other entries of column j. 

	Arguments:
	labels - vector containing example labels
	num_classes - number of possible classes, "depth" of one-hot matrix

	Returns:
	one_hot - matrix that holds a one in the k-th row of each column
	'''

	# Create a tf.constant equal to C (depth), name it 'C'.
	C = tf.constant(num_classes, name="C")

	# Use tf.one_hot, be careful with the axis 
	one_hot_matrix = tf.one_hot(labels, C, axis=0)

	# Create the session
	sess = tf.Session()

	# Run the session
	one_hot = sess.run(one_hot_matrix)

	# Close the session
	sess.close()

	return np.squeeze(one_hot)

def forward_propagation(X, parameters):  
	n_layers = len(parameters) // 2

	A = X;
	for i in range(1,n_layers+1):
		# Retrieve the parameters from the dictionary "parameters" 
		W = parameters['W'+str(i)]
		b = parameters['b'+str(i)]

		# Z[l+1] = W[l]*A[l] + b[l]
		Z = tf.add(tf.matmul(W,A),b)

		# Calculate activation for all layers except the last one
		if i is not n_layers:
			A = tf.nn.relu(Z)
	                                                         
	# Return output of last linear unit to compute_cost
	return Z

def compute_cost(logits, labels):
	"""
	Computes the cost

	Arguments:
	Z - output of forward propagation (output of the last LINEAR unit)
	Y - "true" labels vector placeholder, same shape as Z

	Returns:
	cost - Tensor of the cost function
	"""

	# to fit the tensorflow requirement for tf.nn.softmax_cross_entropy_with_logits(...,...)
	logits = tf.transpose(logits)
	labels = tf.transpose(labels)

	cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=labels))

	return cost

def create_minibatches(X_train, Y_train, num_minibatches, minibatch_size, rem):
	minibatches = []

	for i in range(0,num_minibatches-1):
		minibatches.append((X_train[:,i*minibatch_size:(i+1)*minibatch_size], Y_train[:,i*minibatch_size:(i+1)*minibatch_size]))

	if(rem is not 0):
		minibatches.append((X_train[:,num_minibatches*minibatch_size:], Y_train[:,num_minibatches*minibatch_size:]))

	return minibatches

def model(X_train, Y_train, X_dev, Y_dev, learning_rate = 0.0001,
          num_epochs = 1500, minibatch_size = 32, print_cost = True):
	tf.reset_default_graph()

	n_x = X_train.shape[0]  # Number of pixels in each image / number of input features                
	n_y = Y_train.shape[0]  # Number of classes (10 classes: digits 0-9)
	m   = X_train.shape[1]  # Number of examples                       
	costs = []              # Keep track of model's cost after each epoch for plotting

	# Compute weights and biases matrix dimensions
	layer_sizes = [28**2, 14, 14, 10] # Number of units per layer
	nn_dims = compute_matrix_dims(layer_sizes)

	# Construct Tensorflow graph
	X, Y       = create_placeholders(n_x, n_y)
	parameters = initialize_parameters(nn_dims)
	lin_out    = forward_propagation(X, parameters)
	cost       = compute_cost(lin_out, Y)
	optimizer  = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

	# Initialize all the variables
	init = tf.global_variables_initializer()

	# Run Tensorflow Session
	with tf.Session() as sess:
		# For TensorBoard visualization
		writer = tf.summary.FileWriter('./graphs', sess.graph)

		# Run initialization
		sess.run(init)

		# bef = process_time()	# Time minibatch creation time
		# # Form minibatches (random shuffling not needed since dataset is shuffled during load_dataset())
		# num_minibatches = int(m / minibatch_size)
		# rem = m % minibatch_size;
		# minibatches = create_minibatches(X_train, Y_train, num_minibatches, minibatch_size, rem)
		# aft = process_time(); diff = aft-bef   
		# print ("Minibatch Creation Time: {0:.5f} s | {1:.5f} min".format(diff, diff/60))

		# # Mini-batch stochastic training loop...
		# bef = process_time()	# Time training time
		# epoch_bef = bef
		# for epoch in range(1,num_epochs+1):
		# 	epoch_cost = 0.0

		# 	for minibatch in minibatches:
		# 		(minibatch_X, minibatch_Y) = minibatch

		# 		_, minibatch_cost = sess.run([optimizer,cost], feed_dict={X: minibatch_X, Y: minibatch_Y})

		# 		epoch_cost += minibatch_cost / num_minibatches
 
		# 	# Print the cost and computation time per 100 epochs
		# 	if print_cost and epoch % 100 == 0:
		# 		print ("Cost after epoch %i: %f" % (epoch, epoch_cost), end = " ")
		# 		epoch_aft = process_time(); epoch_diff = epoch_aft-epoch_bef
		# 		epoch_bef = process_time()
		# 		print ("| {0:.5f} s | {1:.5f} min".format(epoch_diff, epoch_diff/60))
		# 	if print_cost and epoch % 10 == 0:
		# 		costs.append(epoch_cost)
		# aft = process_time(); diff = aft-bef   
		# print("Total Training Time: {0:.2f} s , {1:.2f} min".format(diff, diff/60))

		parameters = np.load('trained_parameters.npy')
		# Plot costs over epochs
		plt.plot(np.squeeze(costs))
		plt.ylabel("Cost")
		plt.xlabel("Iterations (Per 10 Iter.)")
		plt.title("Learning rate =" + str(learning_rate))
		plt.savefig("CostCurve_" + str(learning_rate) + ".png")

		# Acquire trained parameters
		parameters = sess.run(parameters)
		print ("Training complete!")

		# Calculate the number of correct predictions
		predictions = tf.argmax(lin_out)
		predictions = predictions.eval({X: X_dev, Y: Y_dev}).squeeze()
		print(predictions) # DEBUG, for visual confirmation that it's one hot or not
		correct_prediction = tf.equal(tf.argmax(lin_out), tf.argmax(Y), name="predict-compare")

		# Calculate accuracy on the test set
		accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

		# Acquire indices of incorrectly labeled examples
		errors = tf.where(tf.not_equal(tf.argmax(lin_out), tf.argmax(Y)))
		errors = errors.eval({X: X_dev, Y: Y_dev}).squeeze() # TODO: .squeeze here?

		print ("Train Accuracy:", accuracy.eval({X: X_train, Y: Y_train}))
		print ("Dev Accuracy:", accuracy.eval({X: X_dev, Y: Y_dev}))

		sess.close()
		writer.close()

	return parameters, errors, predictions

def predict_on_test(trained_params):
	# Get unlabeled testing examples
	X_eval = load_eval_dataset()

	# Normalize image vectors
	X_eval = X_eval / 255.0

	tf.reset_default_graph()

	n_x = X_eval.shape[0]   # Number of pixels in each image / number of input features                                      

	# Construct Tensorflow graph
	X, _ = create_placeholders(n_x, 10)
	lin_out = forward_propagation(X_eval, trained_params)
	predictions = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels)

	with tf.Session as sess:
		sess.run(predictions)
		sess.close()

	# TODO: Convert this simple print statement to the output specification given by Kaggle
	print(predictions)

	# printToFile("ImageId,Label")
	# for i in range(len(predictions)):
	#     printToFile(i,predictions[i])

# Compare predicted values with incorrect labels
def compare_predictions_with_labels(labels, indices):
	None

# Visualize the incorrectly identified indices
# Indices are into X_dev
def visualize_errors(data, labels, predictions, indices):
	# TEMPORARY, just make a bunch of image files and store in a file
	# for index in indices:
	# 	img = data[:,index].reshape((28,28))
	# 	#plt.title("Label = " + str(labels[index]) + ", Answer = " + str())
	# 	plt.imshow(img)
	# 	#plt.draw()
	# 	plt.savefig("./error_images/" + str(index))

	# Better
	count = 0 
	for i, index in enumerate(indices):
	 	# Get correct labels, 
	 	label_val = labels[index]
	 	mispr_val = predictions[index]
	 	img = data[:,index]

	 	plt.subplot("55" + str(i))
	 	plt.imshow(img)
	 		# TODO: Write Title - "actual value" x "mispredicted value"

	 	# Print first 25 images
	 	count += 1
	 	if count == 25:
	 		break;

	# Save figure to file
	plot.savefig("./error_images")


	# 	# Get erroneous label

	# 	# Get pixel data

	# 	# Draw image to subplot
	# 	plt.subplot(index)

	# 	# Place label information in title

	# 	# Save figure out to file???

#
def analyze_errors():
	None















