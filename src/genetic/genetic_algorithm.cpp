/*
*	This code executes the genetic algorithm on an argument image (size set to ROWSxCOLS)
*	<ITERATIONS> iterations are performed using <NUM_CHILDREN> children, and intermittent bitmaps are generated while executing (one every 100 iterations)
*		The program asks for the name of the bitmap file to be used as the target
*		
*	A random image is generated, and the genetic algorithm uses the hamming distance from the target image as the fitness function.
*	The result (given enough iterations) will be the random image
*/

#include <iostream>
#include <iomanip>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <cstdint>
#include <fstream>
#include <pthread.h>
using namespace std;

#define NUM_WORKERS 2
#define NUM_CHILDREN 500
#define ROWS 283//16
#define COLS 240//32
#define ITERATIONS 10000

// BMP Code pulled from:
// http://cboard.cprogramming.com/c-programming/50007-reading-bitmap-image.html
// scrapedbr's code

//Added Headers for opening files
typedef struct
	{
		char		type[2]; 	// file type
		unsigned int	size; 		// file size in bytes
		unsigned short int reserved1,reserved2;
		unsigned int	offset; 	// offset to image data
	}HEADER;

typedef struct
        {
                unsigned char RGB[3];
        }RGB;

typedef struct
        {
                unsigned int size;
                int width,height;
                unsigned short int planes;
                unsigned short int bpp;
                unsigned int compression;
                unsigned int imagesize;
                int xresolution,yresolution;
                unsigned int colours;
                unsigned int impcolours;
        }INFOHEADER;

//End of Headers for opening files


struct Pixel
{
	uint8_t r;
	uint8_t g;
	uint8_t b;
};

struct LCD
{
	Pixel pixels[ROWS*COLS];
};


int hamming_diff(const LCD* lcd1, const LCD* lcd2);
int generate_child(LCD* child, const LCD* mother, const LCD* father, const LCD* target);

//Added for file handling
FILE* exist(char *name);
void isBMP(FILE* arq,HEADER head,INFOHEADER info);
INFOHEADER readInfo(FILE* arq);
RGB** createMatrix();
void loadImage(FILE* arq, RGB** Matrix);
void writeBMP(RGB **OutMatrix, HEADER head, FILE* arq);
void freeMatrix(RGB **Matrix,INFOHEADER info);

/* Global */
int height, width;


/* 
* Cached best child and hamming distance (from target ) for each child to reduce hamming calculations
*/


/* Index of top two children */
int index_1;
int index_2;

/* Hamming distance of the two top children from target */
int index_1_ham;
int index_2_ham;



LCD target;
//LCD parents[2];
//LCD runnersup[2];

int file_counter = 0;

int main(void)
{
	srand(time(NULL));

	// Local variables for the BMP parser
	FILE *arq; /* the bitmap file 24 bits */
	RGB  **Matrix;
	INFOHEADER info;
	HEADER head;
	char name[32];

	printf("Type the image's name : ");
	scanf("%s",name);

	arq = exist(name);

	// Check passed file to make sure it's a BMP of the correct format
	isBMP(arq,head,info);

	// Parse the file
	info = readInfo(arq);
	height = abs(info.height);
	width = abs(info.width);

	Matrix = createMatrix(); // Create a Matrix to load Pixel values into

	loadImage(arq,Matrix); // Load the file into a Matrix


	for (int i = 0; i < COLS; i++){
		for (int j = 0; j < ROWS; j++){

			// Load the target.pixels from the Matrix; this may be redundant
			target.pixels[j*COLS + i].r = Matrix[j][i].RGB[2];
			target.pixels[j*COLS + i].b = Matrix[j][i].RGB[1];
			target.pixels[j*COLS + i].g = Matrix[j][i].RGB[0];
		}
	}
	
	// LCD objects for the mother and father
	LCD* mother = new LCD;
	LCD* father = new LCD;

	// Set the mother and father LCDs to random values
	for (int i = 0; i < ROWS; i++)
	{
		for (int j = 0; j < COLS; j++)
		{
			mother->pixels[i*COLS + j].r = rand()%256;
			mother->pixels[i*COLS + j].g = rand()%256;
			mother->pixels[i*COLS + j].b = rand()%256;
			father->pixels[i*COLS + j].r = rand()%256;
			father->pixels[i*COLS + j].g = rand()%256;
			father->pixels[i*COLS + j].b = rand()%256;
		}
	}

	// Make sure that the mother is always 'better' than the father
	if (hamming_diff(father, &target) < hamming_diff(mother, &target))
	{
		LCD* temp = mother;
		mother = father;
		father = temp;
	}

	// Create an array of children LCD objects
	LCD* children = new LCD[NUM_CHILDREN];


	// Do the following for every iteration
	for (int t = 0; t < ITERATIONS; t++)
	{

		// Initially, the first two children have the best hamming distance
		index_1 = 0;
		index_2 = 1;

		// Set their hamming distance
		index_1_ham = NULL;
		index_2_ham = NULL;

		for (int c = 0; c < NUM_CHILDREN; c++){

			int child_hamming_distance = generate_child(&children[c], mother, father, &target);

			if(c == 0)
				index_1_ham = child_hamming_distance;
			else if(c == 1){

				if(child_hamming_distance < index_1_ham){
					index_2_ham = index_1_ham;
					index_2 = index_1;
					index_1_ham = child_hamming_distance;
					index_1 = c;
				}else{
					index_2_ham = child_hamming_distance;
				}
			}
			else if(c > 1){

				if( child_hamming_distance < index_1_ham){
					index_2 = index_1;
					index_2_ham = index_1_ham;
					index_1 = c;
					index_1_ham = child_hamming_distance;
				}
				else if( child_hamming_distance < index_2_ham){
					index_2 = c;
					index_2_ham = child_hamming_distance;
				}

			}
		}


		if (index_1_ham < hamming_diff(mother, &target))
		{
			memcpy(father, mother, sizeof(LCD));
			memcpy(mother, &children[index_1], sizeof(LCD));
		
			if(index_2_ham < hamming_diff(father, &target)){
				memcpy(father, &children[index_2], sizeof(LCD));
			}
		}
		else if (index_1_ham < hamming_diff(father, &target))
			memcpy(father, &children[index_1], sizeof(LCD));
		
		cout << "Iteration " << (t + 1) << " best Hamming diff: " << hamming_diff(mother, &target) << endl;


		if(t%2 == 0){
			for (int i = 0; i < COLS; i++){
				for (int j = 0; j < ROWS; j++){

					Matrix[j][i].RGB[2] = mother->pixels[j*COLS + i].r;
					Matrix[j][i].RGB[1] = mother->pixels[j*COLS + i].b;
					Matrix[j][i].RGB[0] = mother->pixels[j*COLS + i].g;
				}
			}

			writeBMP(Matrix,head,arq);
		}
		

		if(index_1_ham < 10000)
			break;

	}

	LCD* best = hamming_diff(mother, &target) < hamming_diff(father, &target) ? mother : father;


	for (int i = 0; i < COLS; i++){
		for (int j = 0; j < ROWS; j++){
			Matrix[j][i].RGB[2] = mother->pixels[j*COLS + i].r;
			Matrix[j][i].RGB[1] = mother->pixels[j*COLS + i].b;
			Matrix[j][i].RGB[0] = mother->pixels[j*COLS + i].g;
		}
	}

		writeBMP(Matrix,head,arq);
	
	/*
	ofstream output;
	output.open("result_serial.ppm");
	output << "P3" << endl
		   << COLS << " " << ROWS << endl
		   << "255" << endl;
	for (int i = 0; i < ROWS; i++)
	{
		for (int j = 0; j < COLS; j++)
			output << (int)(best->pixels[i*COLS + j].r) << " "<< (int)(best->pixels[i*COLS + j].g) << " " << (int)(best->pixels[i*COLS + j].b) << endl;
		output << endl;
	}
	output << endl;
	output.close();

	*/
	freeMatrix(Matrix, info);

	return 0;
}

// Find the hamming distance from lcd1 and lcd2
int hamming_diff(const LCD* lcd1, const LCD* lcd2)
{
	int diff = 0;
	for (int i = 0; i < ROWS; i++)
	{
		for (int j = 0; j < COLS; j++)
		{
			diff += abs(lcd1->pixels[i*COLS + j].r - lcd2->pixels[i*COLS + j].r)
				  + abs(lcd1->pixels[i*COLS + j].g - lcd2->pixels[i*COLS + j].g)
				  + abs(lcd1->pixels[i*COLS + j].b - lcd2->pixels[i*COLS + j].b);
		}
	}
	return diff;
}

// Generate a child, and return it's hamming distance from the target
int generate_child(LCD* child, const LCD* mother, const LCD* father, const LCD* target)
{
	for (int i = 0; i < ROWS; i++)
	{
		for (int j = 0; j < COLS; j++)
		{
			if(rand()%2 == 0){
				child->pixels[i*COLS + j].r = mother->pixels[i*COLS + j].r;
				child->pixels[i*COLS + j].g = mother->pixels[i*COLS + j].g;
				child->pixels[i*COLS + j].b = mother->pixels[i*COLS + j].b;
			}else{
				child->pixels[i*COLS + j].r = father->pixels[i*COLS + j].r;
				child->pixels[i*COLS + j].g = father->pixels[i*COLS + j].g;
				child->pixels[i*COLS + j].b = father->pixels[i*COLS + j].b;
			}
			
		}
		if (rand()%2 == 0)
		{
			switch (rand()%3)
			{
			case 0:
				child->pixels[rand()%(ROWS*COLS)].r = rand()%256;
			case 1:
				child->pixels[rand()%(ROWS*COLS)].g = rand()%256;
			case 2:
				child->pixels[rand()%(ROWS*COLS)].b = rand()%256;
			}
		}
	}

	return hamming_diff(child, target);
}


// ********** Verify if the file exist **********
FILE* exist(char *name)
{
	FILE *tmp;
	tmp = fopen(name,"r+b");
	if (!tmp)
	{
		printf("\nERROR: Incorrect file or not exist!\n");
		exit(0);
	}
	fseek(tmp,0,0);
	return(tmp);
}

// ********** Verify if the file is BMP *********
void isBMP(FILE* arq, HEADER head, INFOHEADER info){
        char type[3];
        unsigned short int bpp;
        fseek(arq,0,0);
        fread(type,1,2,arq);
        type[2] = '\0';

        fseek(arq,28,0);
        fread(&bpp,1,2,arq);

        if (strcmp(type,"BM") || (bpp != 24)){
                printf("\nThe file is not BMP format or is not 24 bits\n");
                exit(0);
        }
}

// ********** Read BMP info from file **********
INFOHEADER readInfo(FILE* arq){
        INFOHEADER info;

        // Image Width in pixels
        fseek(arq,18,0);
        fread(&info.width,1,4,arq);

        // Image Height in pixels
        fseek(arq,22,0);
        fread(&info.height,1,4,arq);

        // Color depth, BPP (bits per pixel)
        fseek(arq,28,0);
        fread(&info.bpp,1,2,arq);

        // Compression type
        // 0 = Normmally
        // 1 = 8 bits per pixel
        // 2 = 4 bits per pixel
        fseek(arq,30,0);
        fread(&info.compression,1,4,arq);

        // Image size in bytes
        fseek(arq,34,0);
        fread(&info.imagesize,1,4,arq);

        // Number of color used (NCL)
        // value = 0 for full color set
        fseek(arq,46,0);
        fread(&info.colours,1,4,arq);

        // Number of important color (NIC)
        // value = 0 means all collors important
        fseek(arq,50,0);
        fread(&info.impcolours,1,4,arq);

        return(info);
}

// ********** Load the BMP into a Matrix **********
void loadImage(FILE* arq, RGB** Matrix){
        int i,j;
        RGB tmp;
        long pos = 51;

        fseek(arq,0,0);

        for (i=0; i<height; i++){
                for (j=0; j<width; j++){
                        pos+= 3;
                        fseek(arq,pos,0);
                        fread(&tmp,(sizeof(RGB)),1,arq);
                        Matrix[i][j] = tmp;
                }
        }
}

// ********** Create Matrix **********
RGB** createMatrix(){
        RGB** Matrix;
        int i;
	printf("sizeof(RGB*): %d, height: %d", sizeof(RGB*), height);
        Matrix = (RGB **) malloc (sizeof (RGB*) * height);
        if (Matrix == NULL){
                perror("***** No memory available *****");
                exit(0);
        }
        for (i=0;i<height;i++){
                Matrix[i] = (RGB *) malloc (sizeof(RGB) * width);
                if (Matrix[i] == NULL){
                perror("***** No memory available *****");
                        exit(0);
                }
        }
        return(Matrix);
}

// ********** Image Output **********
void writeBMP(RGB **Matrix, HEADER head, FILE* arq){

	FILE* out;
	int i,j;
	RGB tmp;
	long pos = 51;

	char header[54];
	fseek(arq,0,0);
	fread(header,54,1,arq);

	char out_file[32];

	sprintf(out_file, "%d_%s", file_counter++, "out.bmp");

	out = fopen(out_file,"w");

	fseek(out,0,0);
	fwrite(header,54,1,out);

	printf("\nMatrix = %c\n",Matrix[0][0].RGB[0]);
	for(i=0;i<height;i++){
		for(j=0;j<width;j++){
			pos+= 3;
			fseek(out,pos,0);
			tmp = Matrix[i][j];
			fwrite(&tmp,(sizeof(RGB)),1,out);
		}
	}
	fflush(out);
	fclose(out);
}

// ********** Free memory allocated for Matrix **********
void freeMatrix(RGB** Matrix,INFOHEADER info)
{
	int i;
	int lines = info.height;

	for (i=0;i<lines;i++){
		free(Matrix[i]);
	}
	free(Matrix);
}

