//Compiled by Uberort v1.2.0
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <string.h>
#include <sys/time.h>

typedef union {
    int64_t i;
    double f;
    void* s;
} Quant;

typedef struct {
    Quant* elements;
    int32_t size;
    int32_t cur_size;
} list;

list* make_list() {
    list* outp = malloc(sizeof(list));
    outp->size = 16;
    outp->cur_size = 0;
    outp->elements = malloc(sizeof(Quant)*16);
    return outp;
}

void destroy_list(list* self) {
    free(self->elements);
    free(self);
}

void append(list* self, Quant n) {
    if (self->size == self->cur_size) {
        self->elements = realloc(self->elements, sizeof(Quant)*self->size*2);
        self->size *= 2;
    }
    self->elements[self->cur_size++] = n;
}

list* array_to_list(Quant* arr, int32_t size) {
    list* outp = malloc(sizeof(list));
    outp->size = size;
    outp->cur_size = size;
    outp->elements = malloc(sizeof(Quant)*size);
    memcpy(outp->elements, arr, sizeof(Quant)*size);
    return outp;
}

Quant getitem(list* self, int32_t n) {
    return self->elements[n];
}

typedef struct {
    Quant key;
    Quant value;
    int32_t next; // index of next pair in case of collision
} KeyValuePair;

typedef struct {
    KeyValuePair* pairs;
    int32_t* table;
    int32_t size;
    int32_t cur_size;
    int32_t pair_count;
} dict;

uint32_t hash_int(Quant a) {
    return a.i*3 + ((a.i%63) << 3);
}

dict* make_dict() {
    dict* outp = malloc(sizeof(dict));
    outp->size = 16;
    outp->cur_size = 0;
    outp->pair_count = 0;
    outp->pairs = malloc(sizeof(KeyValuePair) * outp->size);
    outp->table = malloc(sizeof(int32_t) * outp->size);
    for (int i = 0; i < outp->size; i++) outp->table[i] = -1;
    return outp;
}

void destroy_dict(dict* self) {
    free(self->pairs);
    free(self->table);
    free(self);
}

void resize_and_rehash(dict* self) {
    int32_t old_size = self->size;
    self->size *= 4;
    self->pairs = realloc(self->pairs, sizeof(KeyValuePair) * self->size);
    int32_t* new_table = malloc(sizeof(int32_t) * self->size);
    for (int i = 0; i < self->size; i++) new_table[i] = -1;
    for (int i = 0; i < self->pair_count; i++) {
        uint32_t hash = hash_int(self->pairs[i].key) % self->size;
        self->pairs[i].next = new_table[hash];
        new_table[hash] = i;
    }
    free(self->table);
    self->table = new_table;
}


Quant dict_set(dict* self, Quant key, Quant value) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            self->pairs[pair_index].value = value;
            return value;
        }
        pair_index = self->pairs[pair_index].next;
    }
    if (self->pair_count >= self->size*0.6) resize_and_rehash(self);
    self->pairs[self->pair_count].key = key;
    self->pairs[self->pair_count].value = value;
    self->pairs[self->pair_count].next = self->table[hash];
    self->table[hash] = self->pair_count;
    self->pair_count++;
    self->cur_size++;
    return value;
}

Quant dict_get(dict* self, Quant key) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            return self->pairs[pair_index].value;
        }
        pair_index = self->pairs[pair_index].next;
    }
    printf("Error: dictionary key doesn't exist");
    exit(1);
}


int dict_has(dict* self, Quant key) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            return 1;
            return 1;
        }
        pair_index = self->pairs[pair_index].next;
    }
    return 0;
}

double gauss_pd(double x) {
    return (1.0 / sqrt(2 * M_PI)) * exp(-0.5 * x * x);
}

double gauss_random() {
    // Generate two independent random numbers uniformly distributed in (0, 1)
    double u1 = ((double) rand() / (RAND_MAX));
    double u2 = ((double) rand() / (RAND_MAX));

    // Apply Box-Muller transform
    double z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);

    // z0 is a normally distributed random variable with mean 0 and std deviation 1
    return z0;
}

double current_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

double gauss_cd(double x) {
    return 0.5 * (1 + erf(x / sqrt(2)));
}


int main() {
	srand ( time(NULL) );
	//start of math.number_theory
		int64_t is_prime(int64_t math___p) {
		int64_t math______o_l0 = 1;
		for (int ___c_s_0___l2 = 2; ___c_s_0___l2 <= sqrt(math___p); ___c_s_0___l2++){ //range
			int64_t math___r = ___c_s_0___l2; //inline variable
			if ((!((int64_t) math___p % (int64_t) math___r))) {math______o_l0 = 0; goto ___lbl0;} //none
		}
___lbl0:
		return ((math___p < 2) ? 0 : math______o_l0);
	}
	int64_t gcd(int64_t math___a, int64_t math___b) {
		while ((math___b != 0)) {
		int64_t math___c = ((int64_t) math___a % (int64_t) math___b);
		math___a = math___b;
		math___b = math___c;
	}
	return abs(math___a);
}
	int64_t lcm(int64_t math___a, int64_t math___b) {
	return (((!math___a) || (!math___b)) ? 0 : ((int64_t) (math___a * math___b) / (int64_t) gcd(math___a, math___b)));
}
list* primes_till(int64_t math___n) {
	list* ___outp = make_list();
	list* math______c_h0 = make_list();
	for (int ___c_s_1___l2 = 2; ___c_s_1___l2 <= math___n; ___c_s_1___l2++){ //range
		int64_t math___r = ___c_s_1___l2; //inline variable
		int64_t math______o_l1 = 1;
		for (int math______c_h0___l1 = 0; math______c_h0___l1 < math______c_h0->cur_size; math______c_h0___l1++) {
			int64_t math______c_h0___l2 = getitem(math______c_h0, math______c_h0___l1).i;
			if ((!((int64_t) math___r % (int64_t) math______c_h0___l2))) {math______o_l1 = 0; goto ___lbl1;} //none
		}
___lbl1:
		Quant ___q_p0 = {.i=math___r};
		if (math______o_l1) {append(math______c_h0, ___q_p0);}
	}
	for (int math______c_h0___l1 = 0; math______c_h0___l1 < math______c_h0->cur_size; math______c_h0___l1++) {
		int64_t math______c_h0___l2 = getitem(math______c_h0, math______c_h0___l1).i;
		int64_t math___outp = math______c_h0___l2; //inline variable
		Quant ___q_p1 = {.i=math______c_h0___l2};
		append(___outp, ___q_p1);
	}
	destroy_list(math______c_h0);
	return ___outp;
}
	int64_t is_square(int64_t math___n) {
	return ((math___n < 0) ? 0 : ((pow(((int) sqrt(math___n)), 2)) == math___n));
}
list* factors(int64_t math___n) {
	Quant ___b_a0[2] = {{.i=1}, {.i=math___n}};
	list* math___outp = array_to_list(___b_a0, 2);
	for (int ___c_s_2___l2 = 2; ___c_s_2___l2 <= sqrt(math___n); ___c_s_2___l2++){ //range
		int64_t math___i = ___c_s_2___l2; //inline variable
		if ((!((int64_t) math___n % (int64_t) math___i))) {
			Quant ___q_p2 = {.i=math___i};
			append(math___outp, ___q_p2); //concatenation
			Quant ___q_p3 = {.i=((int64_t) math___n / (int64_t) math___i)};
			append(math___outp, ___q_p3); //concatenation
		}
	}
		list* math______c_h1 = make_list();
	for (int math___outp___l1 = 0; math___outp___l1 < math___outp->cur_size; math___outp___l1++) {
		int64_t math___outp___l2 = getitem(math___outp, math___outp___l1).i;
		Quant ___q_p4 = {.i=math___outp___l2};
		append(math______c_h1, ___q_p4); //sum-up
	}
	return math______c_h1;
destroy_list(math______c_h1);
}
	//end of math.number_theory
	int64_t main___ia = 4;
	double main___fb = 7.0;
	double main___ti_a = 6.75;
	printf("%s\n", "Hello World!");
	printf("%lf\n", (main___ia + main___fb));
	Quant ___b_a0[4] = {{.i=1}, {.i=3}, {.i=5}, {.i=9}};
	list* main___sia = array_to_list(___b_a0, 4);
	Quant ___b_a1[3] = {{.i=1}, {.i=9}, {.i=40}};
	list* main___sib = array_to_list(___b_a1, 3);
			list* main______p_s0 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		for (int main___sib___l1 = 0; main___sib___l1 < main___sib->cur_size; main___sib___l1++) {
			int64_t main___sib___l2 = getitem(main___sib, main___sib___l1).i;
			Quant ___q_p0 = {.i=(main___sia___l2 + main___sib___l2)};
			append(main______p_s0, ___q_p0); //print
		}
	}
	printf("{");
	for (int main______p_s0_1 = 0; main______p_s0_1 < main______p_s0->cur_size; main______p_s0_1++) {
		printf("%ld", getitem(main______p_s0, main______p_s0_1).i);
		if (main______p_s0_1 != main______p_s0->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s0);
		list* main______p_s1 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		Quant ___q_p1 = {.f=sin(main___sia___l2)};
		append(main______p_s1, ___q_p1); //print
	}
	printf("{");
	for (int main______p_s1_1 = 0; main______p_s1_1 < main______p_s1->cur_size; main______p_s1_1++) {
		printf("%lf", getitem(main______p_s1, main______p_s1_1).f);
		if (main______p_s1_1 != main______p_s1->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s1);
		list* main______p_s2 = make_list();
		list* main______c_h0 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		Quant ___q_p2 = {.i=main___sia___l2};
		append(main______c_h0, ___q_p2); //sum-up
	}
	for (int main___sib___l1 = 0; main___sib___l1 < main___sib->cur_size; main___sib___l1++) {
		int64_t main___sib___l2 = getitem(main___sib, main___sib___l1).i;
		Quant ___q_p3 = {.i=main___sib___l2};
	append(main______c_h0, ___q_p3); //concatenation
	}
	for (int main______c_h0___l1 = 0; main______c_h0___l1 < main______c_h0->cur_size; main______c_h0___l1++) {
		int64_t main______c_h0___l2 = getitem(main______c_h0, main______c_h0___l1).i;
		Quant ___q_p4 = {.i=main______c_h0___l2};
		append(main______p_s2, ___q_p4); //print
	}
	printf("{");
	for (int main______p_s2_1 = 0; main______p_s2_1 < main______p_s2->cur_size; main______p_s2_1++) {
		printf("%ld", getitem(main______p_s2, main______p_s2_1).i);
		if (main______p_s2_1 != main______p_s2->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s2);
			list* main______c_h1 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		for (int main___sib___l1 = 0; main___sib___l1 < main___sib->cur_size; main___sib___l1++) {
			int64_t main___sib___l2 = getitem(main___sib, main___sib___l1).i;
			Quant ___q_p5 = {.i=(main___sia___l2 + main___sib___l2)};
			append(main______c_h1, ___q_p5); //long concatenation
		}
	}
	for(int64_t main______c_h1___l1 = 0; main______c_h1___l1 < main______c_h1->cur_size; main______c_h1___l1++) append(main___sib, getitem(main______c_h1, main______c_h1___l1)); //concatenation
		list* main______p_s3 = make_list();
	for (int main___sib___l1 = 0; main___sib___l1 < main___sib->cur_size; main___sib___l1++) {
		int64_t main___sib___l2 = getitem(main___sib, main___sib___l1).i;
		Quant ___q_p6 = {.i=main___sib___l2};
		append(main______p_s3, ___q_p6); //print
	}
	printf("{");
	for (int main______p_s3_1 = 0; main______p_s3_1 < main______p_s3->cur_size; main______p_s3_1++) {
		printf("%ld", getitem(main______p_s3, main______p_s3_1).i);
		if (main______p_s3_1 != main______p_s3->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s3);
		list* main______p_s4 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		Quant ___q_p7 = {.i=(main___sia___l2 + main___sia___l2)};
		append(main______p_s4, ___q_p7); //print
	}
	printf("{");
	for (int main______p_s4_1 = 0; main______p_s4_1 < main______p_s4->cur_size; main______p_s4_1++) {
		printf("%ld", getitem(main______p_s4, main______p_s4_1).i);
		if (main______p_s4_1 != main______p_s4->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s4);
		list* main______p_s5 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		Quant ___q_p8 = {.f=(main___sia___l2 + sin(main___sia___l2))};
		append(main______p_s5, ___q_p8); //print
	}
	printf("{");
	for (int main______p_s5_1 = 0; main______p_s5_1 < main______p_s5->cur_size; main______p_s5_1++) {
		printf("%lf", getitem(main______p_s5, main______p_s5_1).f);
		if (main______p_s5_1 != main______p_s5->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s5);
			list* main______p_s6 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		int64_t main___sia2 = main___sia___l2; //inline variable
		for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
			int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
			Quant ___q_p9 = {.f=(((main___sia___l2 + sin(main___sia___l2)) + (pow(main___sia2, 2))) + cos(main___sia2))};
			append(main______p_s6, ___q_p9); //print
		}
	}
	printf("{");
	for (int main______p_s6_1 = 0; main______p_s6_1 < main______p_s6->cur_size; main______p_s6_1++) {
		printf("%lf", getitem(main______p_s6, main______p_s6_1).f);
		if (main______p_s6_1 != main______p_s6->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s6);
	Quant ___b_a2[4] = {{.i=0}, {.i=1}, {.i=2}, {.i=3}};
	list* main___sia3 = array_to_list(___b_a2, 4);
		list* main______p_s7 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		int64_t main___sia3___l2 = getitem(main___sia3, main___sia___l1).i; //pair
		Quant ___q_p10 = {.f=(((main___sia___l2 + sin(main___sia___l2)) + (pow(main___sia3___l2, 2))) + cos(main___sia3___l2))};
		append(main______p_s7, ___q_p10); //print
	}
	printf("{");
	for (int main______p_s7_1 = 0; main______p_s7_1 < main______p_s7->cur_size; main______p_s7_1++) {
		printf("%lf", getitem(main______p_s7, main______p_s7_1).f);
		if (main______p_s7_1 != main______p_s7->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s7);
	if ((main___ia > 0)) {
		printf("%s\n", "+");
	}
	else if ((main___ia < 0)) {
		printf("%s\n", "-");
	}
	else {
		printf("%s\n", "0");
	}
	int64_t main___sum_of_sia = 0;
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		main___sum_of_sia += main___sia___l2;
	}
	printf("%ld\n", main___sum_of_sia);
	main___sum_of_sia = 0;
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		main___sum_of_sia += main___sia___l2;
	}
	printf("%ld\n", main___sum_of_sia);
	int64_t main______o_l0 = 0;
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		main______o_l0 += main___sia___l2; //sum
	}
	printf("%ld\n", main______o_l0);
	main___sum_of_sia = 0;
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		int64_t main___i = main___sia___l2; //inline variable
		main___sum_of_sia += main___i;
	}
	printf("%ld\n", main___sum_of_sia);
	int64_t main___product_sum = 0;
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		int64_t main___sia3___l2 = getitem(main___sia3, main___sia___l1).i; //pair
		main___product_sum += (main___sia___l2 * main___sia3___l2);
	}
	printf("%ld\n", main___product_sum);
	int64_t main___a = 10;
	int64_t main___b = 15;
		list* main___r1 = make_list();
	for (int ___c_s_0___l2 = 1; ___c_s_0___l2 <= (main___a < main___b ? main___a : main___b); ___c_s_0___l2++){ //range
		Quant ___q_p11 = {.i=___c_s_0___l2};
		append(main___r1, ___q_p11);
	}
	int64_t ___o_l2 = 0;
	int64_t main______o_l1 = 0;
	for (int main___r1___l1 = 0; main___r1___l1 < main___r1->cur_size; main___r1___l1++) {
		int64_t main___r1___l2 = getitem(main___r1, main___r1___l1).i;
		if (((!((int64_t) main___a % (int64_t) main___r1___l2)) && (!((int64_t) main___b % (int64_t) main___r1___l2))) && (___o_l2 < main___r1___l2)) {main______o_l1 = main___r1___l2; ___o_l2 = main___r1___l2;} //max - key
	}
	printf("%ld\n", ((int64_t) (main___a * main___b) / (int64_t) main______o_l1));
		list* main______p_s8 = make_list();
	list* main______c_h2 = make_list();
	for (int main___r1___l1 = 0; main___r1___l1 < main___r1->cur_size; main___r1___l1++) {
		int64_t main___r1___l2 = getitem(main___r1, main___r1___l1).i;
		Quant ___q_p12 = {.i=main___r1___l2};
		if (((!((int64_t) main___a % (int64_t) main___r1___l2)) && (!((int64_t) main___b % (int64_t) main___r1___l2)))) {append(main______c_h2, ___q_p12);}
	}
	for (int main______c_h2___l1 = 0; main______c_h2___l1 < main______c_h2->cur_size; main______c_h2___l1++) {
		int64_t main______c_h2___l2 = getitem(main______c_h2, main______c_h2___l1).i;
		Quant ___q_p13 = {.i=main______c_h2___l2};
		append(main______p_s8, ___q_p13); //print
	}
	printf("{");
	for (int main______p_s8_1 = 0; main______p_s8_1 < main______p_s8->cur_size; main______p_s8_1++) {
		printf("%ld", getitem(main______p_s8, main______p_s8_1).i);
		if (main______p_s8_1 != main______p_s8->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s8);
		list* main___r2 = make_list();
	for (int ___c_s_1___l2 = 1; ___c_s_1___l2 <= 50; ___c_s_1___l2++){ //range
		Quant ___q_p14 = {.i=(___c_s_1___l2 + 1)};
		append(main___r2, ___q_p14);
	}
	list* main___primes = make_list();
	for (int main___r2___l1 = 0; main___r2___l1 < main___r2->cur_size; main___r2___l1++) {
		int64_t main___r2___l2 = getitem(main___r2, main___r2___l1).i;
		int64_t main______o_l3 = 1;
		for (int main___primes___l1 = 0; main___primes___l1 < main___primes->cur_size; main___primes___l1++) {
			int64_t main___primes___l2 = getitem(main___primes, main___primes___l1).i;
			if ((!((int64_t) main___r2___l2 % (int64_t) main___primes___l2))) {main______o_l3 = 0; goto ___lbl0;} //none
		}
___lbl0:
		Quant ___q_p15 = {.i=main___r2___l2};
		if (main______o_l3) {append(main___primes, ___q_p15);}
	}
		list* main______p_s9 = make_list();
	for (int main___primes___l1 = 0; main___primes___l1 < main___primes->cur_size; main___primes___l1++) {
		int64_t main___primes___l2 = getitem(main___primes, main___primes___l1).i;
		Quant ___q_p16 = {.i=main___primes___l2};
		append(main______p_s9, ___q_p16); //print
	}
	printf("{");
	for (int main______p_s9_1 = 0; main______p_s9_1 < main______p_s9->cur_size; main______p_s9_1++) {
		printf("%ld", getitem(main______p_s9, main______p_s9_1).i);
		if (main______p_s9_1 != main______p_s9->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s9);
		list* main______p_s10 = make_list();
	list* main______c_h3 = make_list();
	for (int ___c_s_2___l2 = 0; ___c_s_2___l2 < 60; ___c_s_2___l2++){ //range
		int64_t main___ri = ___c_s_2___l2; //inline variable
		Quant ___q_p17 = {.i=main___ri};
		if (((!((int64_t) main___ri % (int64_t) 3)) && ((int64_t) main___ri % (int64_t) 7))) {append(main______c_h3, ___q_p17);}
	}
	for (int main______c_h3___l1 = 0; main______c_h3___l1 < main______c_h3->cur_size; main______c_h3___l1++) {
		int64_t main______c_h3___l2 = getitem(main______c_h3, main______c_h3___l1).i;
		Quant ___q_p18 = {.i=main______c_h3___l2};
		append(main______p_s10, ___q_p18); //print
	}
	printf("{");
	for (int main______p_s10_1 = 0; main______p_s10_1 < main______p_s10->cur_size; main______p_s10_1++) {
		printf("%ld", getitem(main______p_s10, main______p_s10_1).i);
		if (main______p_s10_1 != main______p_s10->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s10);
		list* main______p_s11 = make_list();
	list* main______c_h4 = make_list();
	for (int ___c_s_3___l2 = 1; ___c_s_3___l2 <= 50; ___c_s_3___l2++){ //range
		int64_t main___range_inline = (___c_s_3___l2 + 1); //inline variable
		int64_t main______o_l4 = 1;
		for (int main______c_h4___l1 = 0; main______c_h4___l1 < main______c_h4->cur_size; main______c_h4___l1++) {
			int64_t main______c_h4___l2 = getitem(main______c_h4, main______c_h4___l1).i;
			if ((!((int64_t) main___range_inline % (int64_t) main______c_h4___l2))) {main______o_l4 = 0; goto ___lbl1;} //none
		}
___lbl1:
		Quant ___q_p19 = {.i=main___range_inline};
		if (main______o_l4) {append(main______c_h4, ___q_p19);}
	}
	for (int main______c_h4___l1 = 0; main______c_h4___l1 < main______c_h4->cur_size; main______c_h4___l1++) {
		int64_t main______c_h4___l2 = getitem(main______c_h4, main______c_h4___l1).i;
		int64_t main___rec_inline = main______c_h4___l2; //inline variable
		Quant ___q_p20 = {.i=main______c_h4___l2};
		append(main______p_s11, ___q_p20); //print
	}
	printf("{");
	for (int main______p_s11_1 = 0; main______p_s11_1 < main______p_s11->cur_size; main______p_s11_1++) {
		printf("%ld", getitem(main______p_s11, main______p_s11_1).i);
		if (main______p_s11_1 != main______p_s11->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s11);
	dict* main___fibs___d = make_dict();
	int64_t main___fibs(int64_t main___i) {
	Quant ___q_p21 = {.i=main___i};
		if (dict_has(main___fibs___d, ___q_p21)) {
			return dict_get(main___fibs___d, ___q_p21).i;
		} else {
			int64_t ___outp = (main___fibs((main___i - 2)) + main___fibs((main___i - 1)));
			Quant ___q_p22 = {.i=___outp};
			return dict_set(main___fibs___d, ___q_p21, ___q_p22).i;
		}
	}
	Quant ___q_p23 = {.i=0};
	Quant ___q_p24 = {.i=1};
	dict_set(main___fibs___d, ___q_p23, ___q_p24);
	Quant ___q_p25 = {.i=1};
	Quant ___q_p26 = {.i=1};
	dict_set(main___fibs___d, ___q_p25, ___q_p26);
	for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("%ld, ", main___fibs(___l_var));
	printf("%ld...\n", main___fibs(16));
	printf("%ld\n", main___fibs(5));
		int64_t main___fibs___l2 = 0;
	for (int main___fibs___l2___l1 = 0; 1; main___fibs___l2___l1++) {
		main___fibs___l2 = main___fibs(main___fibs___l2___l1);
		if ((main___fibs___l2 > 9000)) goto ___lbl2; //first
	}
___lbl2:
	printf("%ld\n", main___fibs___l2);
	double square(double main___x) {
		return (pow(main___x, 2));
	}
	printf("%lf\n", square(7.3));
		list* main______p_s12 = make_list();
	for (int main___sia___l1 = 0; main___sia___l1 < main___sia->cur_size; main___sia___l1++) {
		int64_t main___sia___l2 = getitem(main___sia, main___sia___l1).i;
		Quant ___q_p27 = {.f=square(main___sia___l2)};
		append(main______p_s12, ___q_p27); //print
	}
	printf("{");
	for (int main______p_s12_1 = 0; main______p_s12_1 < main______p_s12->cur_size; main______p_s12_1++) {
		printf("%lf", getitem(main______p_s12, main______p_s12_1).f);
		if (main______p_s12_1 != main______p_s12->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s12);
	int64_t ff(double main___x) {
		return ((main___x < 2) ? 1 : (ff((main___x - 1)) + ff((main___x - 2))));
	}
		int64_t number_of_divisors(int64_t main___x) {
		int64_t main______o_l5 = 1;
		list* main______c_h5 = make_list();
		for (int ___c_s_4___l2 = 1; ___c_s_4___l2 <= main___x; ___c_s_4___l2++){ //range
			int64_t main___r3 = (___c_s_4___l2 + 1); //inline variable
			int64_t main______o_l6 = 1;
			for (int main______c_h5___l1 = 0; main______c_h5___l1 < main______c_h5->cur_size; main______c_h5___l1++) {
				int64_t main______c_h5___l2 = getitem(main______c_h5, main______c_h5___l1).i;
				if ((!((int64_t) main___r3 % (int64_t) main______c_h5___l2))) {main______o_l6 = 0; goto ___lbl3;} //none
			}
___lbl3:
			Quant ___q_p28 = {.i=main___r3};
			if (main______o_l6) {append(main______c_h5, ___q_p28);}
		}
		for (int main______c_h5___l1 = 0; main______c_h5___l1 < main______c_h5->cur_size; main______c_h5___l1++) {
			int64_t main______c_h5___l2 = getitem(main______c_h5, main______c_h5___l1).i;
			int64_t main___all_primes = main______c_h5___l2; //inline variable
				int64_t main___expon = 0;
			for (main___expon = 0; 1; main___expon++) {
				if (((int64_t) main___x % (int64_t) (pow(main______c_h5___l2, main___expon)))) goto ___lbl4; //first
			}
___lbl4:
			main______o_l5 *= main___expon; //product
		}
		destroy_list(main______c_h5);
		return main______o_l5;
	}
	printf("%ld\n", number_of_divisors(840));
		int64_t main___i = 0;
	for (main___i = 0; 1; main___i++) {
		if ((number_of_divisors(main___i) > 32)) goto ___lbl5; //first
	}
___lbl5:
	printf("%ld\n", main___i);
	int64_t factorial(int64_t main___a) {
		int64_t main___outp = 1;
		for (int ___c_s_5___l2 = 1; ___c_s_5___l2 <= main___a; ___c_s_5___l2++){ //range
			int64_t main___i = ___c_s_5___l2; //inline variable
			main___outp *= main___i;
		}
		return main___outp;
	}
	printf("%ld\n", factorial(12));
		int64_t factorial_ol(int64_t main___a) {
		int64_t main______o_l7 = 1;
		for (int ___c_s_6___l2 = 1; ___c_s_6___l2 <= main___a; ___c_s_6___l2++){ //range
			main______o_l7 *= ___c_s_6___l2; //product
		}
		return main______o_l7;
	}
	printf("%ld\n", factorial_ol(12));
	typedef struct {
		double x;
		double y;
	} Vec2;
		double magnitude(Vec2* main___v) {
		return sqrt(((pow(main___v->x, 2)) + (pow(main___v->y, 2))));
	}
	Vec2 ___s_p___s_p0 = {.x = 8, .y = 15};
	Vec2* ___s_p___s_p0_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p0_1, &___s_p___s_p0, sizeof(Vec2));
	printf("%lf\n", magnitude(___s_p___s_p0_1));
	typedef struct {
		Vec2* v;
		int64_t d;
		double f;
	} ComplexContainer;
	Vec2 ___s_p___s_p2 = {.x = 17, .y = 4};
	Vec2* ___s_p___s_p2_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p2_1, &___s_p___s_p2, sizeof(Vec2));
	ComplexContainer ___s_p___s_p1 = {.v = ___s_p___s_p2_1, .d = 5, .f = (-(17.4))};
	ComplexContainer* ___s_p___s_p1_1 = malloc(sizeof(ComplexContainer));
	memcpy(___s_p___s_p1_1, &___s_p___s_p1, sizeof(ComplexContainer));
	ComplexContainer* main___cc = ___s_p___s_p1_1;
	printf("ComplexContainer(v: Vec2(x: %lf, y: %lf), d: %ld, f: %lf)\n", ((Vec2*) ((ComplexContainer*) main___cc)->v)->x, ((Vec2*) ((ComplexContainer*) main___cc)->v)->y, ((ComplexContainer*) main___cc)->d, ((ComplexContainer*) main___cc)->f);
	dict* main___asd___d = make_dict();
			Vec2* main___asd(int64_t main___i) {
	Quant ___q_p29 = {.i=main___i};
		if (dict_has(main___asd___d, ___q_p29)) {
					return dict_get(main___asd___d, ___q_p29).s;
		} else {
	Vec2 ___s_p___s_p3 = {.x = (2 * main___i), .y = (pow(main___i, 2))};
	Vec2* ___s_p___s_p3_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p3_1, &___s_p___s_p3, sizeof(Vec2));
			Vec2* ___outp = ___s_p___s_p3_1;
			Vec2* main______c_p0 = malloc(sizeof(Vec2));
			memcpy(main______c_p0, ___outp, sizeof(Vec2));
			Quant ___q_p30 = {.s=main______c_p0};
			free(___s_p___s_p3_1);
			return dict_set(main___asd___d, ___q_p29, ___q_p30).s;
		}
	}
		Vec2* main___asd___l2 = 0;
	for (int main___asd___l2___l1 = 0; 1; main___asd___l2___l1++) {
		main___asd___l2 = main___asd(main___asd___l2___l1);
		if ((magnitude(main___asd___l2) > 30)) goto ___lbl6; //first
	}
___lbl6:
	printf("Vec2(x: %lf, y: %lf)\n", ((Vec2*) main___asd___l2)->x, ((Vec2*) main___asd___l2)->y);
		Vec2* to_vec(int64_t main___x) {
		Vec2 ___s_p___s_p4 = {.x = main___x, .y = main___x};
		Vec2* ___s_p___s_p4_1 = malloc(sizeof(Vec2));
		memcpy(___s_p___s_p4_1, &___s_p___s_p4, sizeof(Vec2));
		Vec2* main______c_p1 = malloc(sizeof(Vec2));
		memcpy(main______c_p1, ___s_p___s_p4_1, sizeof(Vec2));
		free(___s_p___s_p4_1);
		return main______c_p1;
	}
	printf("Vec2(x: %lf, y: %lf)\n", ((Vec2*) to_vec(8))->x, ((Vec2*) to_vec(8))->y);
	Vec2* main______i_v0 = malloc(sizeof(Vec2));
	scanf("Vec2(x: %lf, y: %lf)", &(((Vec2*) main______i_v0)->x), &(((Vec2*) main______i_v0)->y));
	Vec2* main___v = main______i_v0;
	printf("%lf\n", magnitude(main___v));
		list* main______p_s13 = make_list();
	for (int ___c_s_7 = 0; ___c_s_7 < 5; ___c_s_7++){
		double ___c_s_8___l2 = ((1 - (-(1))) * ((float)rand() / RAND_MAX)) + (-(1)); //random
		Quant ___q_p31 = {.f=___c_s_8___l2};
		append(main______p_s13, ___q_p31); //print
	}
	printf("{");
	for (int main______p_s13_1 = 0; main______p_s13_1 < main______p_s13->cur_size; main______p_s13_1++) {
		printf("%lf", getitem(main______p_s13, main______p_s13_1).f);
		if (main______p_s13_1 != main______p_s13->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s13);
			list* main___ran_vecs = make_list();
	for (int ___c_s_9 = 0; ___c_s_9 < 5000; ___c_s_9++){
		double ___c_s_10___l2 = ((1 - (-(1))) * ((float)rand() / RAND_MAX)) + (-(1)); //random
		for (int ___c_s_11 = 0; ___c_s_11 < 500; ___c_s_11++){
			double ___c_s_12___l2 = ((1 - (-(1))) * ((float)rand() / RAND_MAX)) + (-(1)); //random
	Vec2 ___s_p___s_p5 = {.x = ___c_s_10___l2, .y = ___c_s_12___l2};
			Vec2* ___s_p___s_p5_1 = malloc(sizeof(Vec2));
			memcpy(___s_p___s_p5_1, &___s_p___s_p5, sizeof(Vec2));
			Vec2* main______c_p2 = malloc(sizeof(Vec2));
			memcpy(main______c_p2, ___s_p___s_p5_1, sizeof(Vec2));
			Quant ___q_p32 = {.s=main______c_p2};
			append(main___ran_vecs, ___q_p32);
		free(___s_p___s_p5_1);
		}
	}
	int ___o_l8_counter = 0;
	int64_t main______o_l8 = 0;
	for (int main___ran_vecs___l1 = 0; main___ran_vecs___l1 < main___ran_vecs->cur_size; main___ran_vecs___l1++) {
		Vec2* main___ran_vecs___l2 = getitem(main___ran_vecs, main___ran_vecs___l1).s;
		main______o_l8 += (((pow(main___ran_vecs___l2->x, 2)) + (pow(main___ran_vecs___l2->y, 2))) < 1); ___o_l8_counter++; //average
	}
	printf("%lf\n", ((float) main______o_l8 / ___o_l8_counter * 4));
	void check_if_negative(int64_t main___e) {
	}
	check_if_negative(6);
	void check_if_divisible(int64_t main___a, int64_t main___b) {
	}
	check_if_divisible(11, 3);
		list* main______p_s14 = make_list();
	list* main______c_h6 = make_list();
	for (int main___r2___l1 = 0; main___r2___l1 < main___r2->cur_size; main___r2___l1++) {
		int64_t main___r2___l2 = getitem(main___r2, main___r2___l1).i;
		Quant ___q_p33 = {.i=main___r2___l2};
		if (is_square(main___r2___l2)) {append(main______c_h6, ___q_p33);}
	}
	for (int main______c_h6___l1 = 0; main______c_h6___l1 < main______c_h6->cur_size; main______c_h6___l1++) {
		int64_t main______c_h6___l2 = getitem(main______c_h6, main______c_h6___l1).i;
		Quant ___q_p34 = {.i=main______c_h6___l2};
		append(main______p_s14, ___q_p34); //print
	}
	printf("{");
	for (int main______p_s14_1 = 0; main______p_s14_1 < main______p_s14->cur_size; main______p_s14_1++) {
		printf("%ld", getitem(main______p_s14, main______p_s14_1).i);
		if (main______p_s14_1 != main______p_s14->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(main______p_s14);
	destroy_list(main______c_h0);
	destroy_list(main______c_h1);
	destroy_list(main___r1);
	destroy_list(main______c_h2);
	destroy_list(main___r2);
	destroy_list(main___primes);
	destroy_list(main______c_h3);
	destroy_list(main______c_h4);
	destroy_dict(main___fibs___d);
	free(___s_p___s_p0_1);
	free(___s_p___s_p2_1);
	free(___s_p___s_p1_1);
	for (int main___asd___d___l1 = 0; main___asd___d___l1 < main___asd___d->cur_size; main___asd___d___l1++) {
		free(main___asd___d->pairs[main___asd___d___l1].value.s);
	}
	destroy_dict(main___asd___d);
	for (int main___ran_vecs___l1 = 0; main___ran_vecs___l1 < main___ran_vecs->cur_size; main___ran_vecs___l1++) {
		free(getitem(main___ran_vecs, main___ran_vecs___l1).s);
	}
	destroy_list(main___ran_vecs);
	destroy_list(main______c_h6);
}
