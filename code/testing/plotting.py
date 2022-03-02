def dict_format(data_dict):
	'''
	Input:
		data_dict: Dictionary. Keys are x-values, values 
			are y-axis.
	Returns:
		x_vec: Tuple. Sorted keys.
		y_vec: Tuple. Values, index-matched to x_vec.
	'''
	lsts = sorted(data_dict.items())
	x_vec, y_vec = zip(*lsts)
	return x_vec, y_vec