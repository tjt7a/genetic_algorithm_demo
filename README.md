Genetic Algorithm Demo
=============

This project will visually demonstrate the genetic algorithm. The genetic algorithm is an optimization algorithm inspired by Darwin’s theory of natural selection that can be used to solve large optimization problems that cannot be quickly solved by other methods.  Initially, two sub-optimal solutions are generated; these are the parents.  Using them, a ‘crossover’ is performed, where a child solution containing features randomly chosen from each parent is generated, much like how a biological child’s genes are chosen at random from its parents.  This is performed many times.  Next, a ‘tournament’ is held, where each child and their parents are ranked according to how close to optimal they is.  The top two are kept for the next generation and the process is repeated until a satisfactory solution is converged upon.  Additionally, in each child there is a chance that its features will mutate, or randomize, in order to prevent reaching a local optimum rather than a global one.

Our project will demonstrate the genetic algorithm by using it to transform an image composed of random pixels to a specific target image.  Each generation, the the two images whose Hamming distance from the target image, calculated by summing the difference in each red, green, and blue component of each pixel with the corresponding component of the target images’ pixels, are the least will be allowed to continue and form the “parents” of the next generation.  Over several generations, the parents’ images will converge on the target image.



