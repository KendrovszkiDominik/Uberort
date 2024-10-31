//Compiled by Uberort v1.1.0
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
	int64_t ia = 4;
	double fb = 7.0;
	double ti_a = 6.75;
	printf("%f\n", (ia + fb));
	Quant ___b_a0[4] = {{.i=1}, {.i=3}, {.i=5}, {.i=9}};
	list* sia = array_to_list(___b_a0, 4);
	Quant ___b_a1[3] = {{.i=1}, {.i=9}, {.i=40}};
	list* sib = array_to_list(___b_a1, 3);
			list* ___p_s0 = make_list();
	for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
		int64_t sia___l2 = getitem(sia, sia___l1).i;
		for (int sib___l1 = 0; sib___l1 < sib->cur_size; sib___l1++) {
			int64_t sib___l2 = getitem(sib, sib___l1).i;
			Quant ___q_p0 = {.i=(sia___l2 + sib___l2)};
			append(___p_s0, ___q_p0); //print
		}
	}
	printf("{");
	for (int ___p_s0_1 = 0; ___p_s0_1 < ___p_s0->cur_size; ___p_s0_1++) {
		printf("%d", getitem(___p_s0, ___p_s0_1).i);
		if (___p_s0_1 != ___p_s0->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s0);
		list* ___p_s1 = make_list();
	for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
		int64_t sia___l2 = getitem(sia, sia___l1).i;
		Quant ___q_p1 = {.i=(sia___l2 + sia___l2)};
		append(___p_s1, ___q_p1); //print
	}
	printf("{");
	for (int ___p_s1_1 = 0; ___p_s1_1 < ___p_s1->cur_size; ___p_s1_1++) {
		printf("%d", getitem(___p_s1, ___p_s1_1).i);
		if (___p_s1_1 != ___p_s1->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s1);
		list* ___p_s2 = make_list();
	for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
		int64_t sia___l2 = getitem(sia, sia___l1).i;
		Quant ___q_p2 = {.f=(sia___l2 + sin(sia___l2))};
		append(___p_s2, ___q_p2); //print
	}
	printf("{");
	for (int ___p_s2_1 = 0; ___p_s2_1 < ___p_s2->cur_size; ___p_s2_1++) {
		printf("%f", getitem(___p_s2, ___p_s2_1).f);
		if (___p_s2_1 != ___p_s2->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s2);
			list* ___p_s3 = make_list();
	for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
		int64_t sia___l2 = getitem(sia, sia___l1).i;
		int64_t sia2 = sia___l2; //inline variable
		for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
			int64_t sia___l2 = getitem(sia, sia___l1).i;
			Quant ___q_p3 = {.f=(((sia___l2 + sin(sia___l2)) + (pow(sia2, 2))) + cos(sia2))};
			append(___p_s3, ___q_p3); //print
		}
	}
	printf("{");
	for (int ___p_s3_1 = 0; ___p_s3_1 < ___p_s3->cur_size; ___p_s3_1++) {
		printf("%f", getitem(___p_s3, ___p_s3_1).f);
		if (___p_s3_1 != ___p_s3->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s3);
	int64_t a = 10;
	int64_t b = 15;
		list* r1 = make_list();
	for (int ___c_s_0___l2 = 1; ___c_s_0___l2 <= (a < b ? a : b); ___c_s_0___l2++){ //mrange
		Quant ___q_p4 = {.i=___c_s_0___l2};
		append(r1, ___q_p4);
	}
	int64_t ___o_l1 = 0;
	int64_t ___o_l0 = 0;
	for (int r1___l1 = 0; r1___l1 < r1->cur_size; r1___l1++) {
		int64_t r1___l2 = getitem(r1, r1___l1).i;
		if (((!((int) a % (int) r1___l2)) && (!((int) b % (int) r1___l2))) && (___o_l1 < r1___l2)) {___o_l0 = r1___l2; ___o_l1 = r1___l2;} //max - key
	}
	printf("%d\n", ((int) (a * b) / (int) ___o_l0));
		list* ___p_s4 = make_list();
	list* ___c_h0 = make_list();
	for (int r1___l1 = 0; r1___l1 < r1->cur_size; r1___l1++) {
		int64_t r1___l2 = getitem(r1, r1___l1).i;
		Quant ___q_p5 = {.i=r1___l2};
		if (((!((int) a % (int) r1___l2)) && (!((int) b % (int) r1___l2)))) {append(___c_h0, ___q_p5);}
	}
	for (int ___c_h0___l1 = 0; ___c_h0___l1 < ___c_h0->cur_size; ___c_h0___l1++) {
		int64_t ___c_h0___l2 = getitem(___c_h0, ___c_h0___l1).i;
		Quant ___q_p6 = {.i=___c_h0___l2};
		append(___p_s4, ___q_p6); //print
	}
	printf("{");
	for (int ___p_s4_1 = 0; ___p_s4_1 < ___p_s4->cur_size; ___p_s4_1++) {
		printf("%d", getitem(___p_s4, ___p_s4_1).i);
		if (___p_s4_1 != ___p_s4->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s4);
		list* r2 = make_list();
	for (int ___c_s_1___l2 = 1; ___c_s_1___l2 <= 50; ___c_s_1___l2++){ //mrange
		Quant ___q_p7 = {.i=(___c_s_1___l2 + 1)};
		append(r2, ___q_p7);
	}
	list* primes = make_list();
	for (int r2___l1 = 0; r2___l1 < r2->cur_size; r2___l1++) {
		int64_t r2___l2 = getitem(r2, r2___l1).i;
		int64_t ___o_l2 = 1;
		for (int primes___l1 = 0; primes___l1 < primes->cur_size; primes___l1++) {
			int64_t primes___l2 = getitem(primes, primes___l1).i;
			if ((!((int) r2___l2 % (int) primes___l2))) {___o_l2 = 0; goto ___lbl0;} //none
		}
___lbl0:
		Quant ___q_p8 = {.i=r2___l2};
		if (___o_l2) {append(primes, ___q_p8);}
	}
		list* ___p_s5 = make_list();
	for (int primes___l1 = 0; primes___l1 < primes->cur_size; primes___l1++) {
		int64_t primes___l2 = getitem(primes, primes___l1).i;
		Quant ___q_p9 = {.i=primes___l2};
		append(___p_s5, ___q_p9); //print
	}
	printf("{");
	for (int ___p_s5_1 = 0; ___p_s5_1 < ___p_s5->cur_size; ___p_s5_1++) {
		printf("%d", getitem(___p_s5, ___p_s5_1).i);
		if (___p_s5_1 != ___p_s5->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s5);
		list* ___p_s6 = make_list();
	list* ___c_h1 = make_list();
	for (int ___c_s_2___l2 = 0; ___c_s_2___l2 < 60; ___c_s_2___l2++){ //range
		int64_t ri = ___c_s_2___l2; //inline variable
		Quant ___q_p10 = {.i=ri};
		if (((!((int) ri % (int) 3)) && ((int) ri % (int) 7))) {append(___c_h1, ___q_p10);}
	}
	for (int ___c_h1___l1 = 0; ___c_h1___l1 < ___c_h1->cur_size; ___c_h1___l1++) {
		int64_t ___c_h1___l2 = getitem(___c_h1, ___c_h1___l1).i;
		Quant ___q_p11 = {.i=___c_h1___l2};
		append(___p_s6, ___q_p11); //print
	}
	printf("{");
	for (int ___p_s6_1 = 0; ___p_s6_1 < ___p_s6->cur_size; ___p_s6_1++) {
		printf("%d", getitem(___p_s6, ___p_s6_1).i);
		if (___p_s6_1 != ___p_s6->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s6);
		list* ___p_s7 = make_list();
	list* ___c_h2 = make_list();
	for (int ___c_s_3___l2 = 1; ___c_s_3___l2 <= 50; ___c_s_3___l2++){ //mrange
		int64_t range_inline = (___c_s_3___l2 + 1); //inline variable
		int64_t ___o_l3 = 1;
		for (int ___c_h2___l1 = 0; ___c_h2___l1 < ___c_h2->cur_size; ___c_h2___l1++) {
			int64_t ___c_h2___l2 = getitem(___c_h2, ___c_h2___l1).i;
			if ((!((int) range_inline % (int) ___c_h2___l2))) {___o_l3 = 0; goto ___lbl1;} //none
		}
___lbl1:
		Quant ___q_p12 = {.i=range_inline};
		if (___o_l3) {append(___c_h2, ___q_p12);}
	}
	for (int ___c_h2___l1 = 0; ___c_h2___l1 < ___c_h2->cur_size; ___c_h2___l1++) {
		int64_t ___c_h2___l2 = getitem(___c_h2, ___c_h2___l1).i;
		int64_t rec_inline = ___c_h2___l2; //inline variable
		Quant ___q_p13 = {.i=___c_h2___l2};
		append(___p_s7, ___q_p13); //print
	}
	printf("{");
	for (int ___p_s7_1 = 0; ___p_s7_1 < ___p_s7->cur_size; ___p_s7_1++) {
		printf("%d", getitem(___p_s7, ___p_s7_1).i);
		if (___p_s7_1 != ___p_s7->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s7);
	dict* fibs___d = make_dict();
	int64_t fibs(int64_t i) {
	Quant ___q_p14 = {.i=i};
		if (dict_has(fibs___d, ___q_p14)) {
			return dict_get(fibs___d, ___q_p14).i;
		} else {
			int64_t ___outp = (fibs((i - 2)) + fibs((i - 1)));
			Quant ___q_p15 = {.i=___outp};
			return dict_set(fibs___d, ___q_p14, ___q_p15).i;
		}
	}
	Quant ___q_p16 = {.i=0};
	Quant ___q_p17 = {.i=1};
	dict_set(fibs___d, ___q_p16, ___q_p17);
	Quant ___q_p18 = {.i=1};
	Quant ___q_p19 = {.i=1};
	dict_set(fibs___d, ___q_p18, ___q_p19);
	for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("%d, ", fibs(___l_var));
	printf("%d...\n", fibs(16));
	printf("%d\n", fibs(5));
		int64_t fibs___l2 = 0;
	for (int fibs___l2___l1 = 0; 1; fibs___l2___l1++) {
		fibs___l2 = fibs(fibs___l2___l1);
		if ((fibs___l2 > 9000)) goto ___lbl2; //first
	}
___lbl2:
	printf("%d\n", fibs___l2);
	double square(double x) {
		return (pow(x, 2));
	}
	printf("%f\n", square(7.3));
		list* ___p_s8 = make_list();
	for (int sia___l1 = 0; sia___l1 < sia->cur_size; sia___l1++) {
		int64_t sia___l2 = getitem(sia, sia___l1).i;
		Quant ___q_p20 = {.f=square(sia___l2)};
		append(___p_s8, ___q_p20); //print
	}
	printf("{");
	for (int ___p_s8_1 = 0; ___p_s8_1 < ___p_s8->cur_size; ___p_s8_1++) {
		printf("%f", getitem(___p_s8, ___p_s8_1).f);
		if (___p_s8_1 != ___p_s8->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s8);
	int64_t ff(double x) {
		return ((x < 2) ? 1 : (ff((x - 1)) + ff((x - 2))));
	}
		int64_t number_of_divisors(int64_t x) {
		int64_t ___o_l4 = 1;
		list* ___c_h3 = make_list();
		for (int ___c_s_4___l2 = 1; ___c_s_4___l2 <= x; ___c_s_4___l2++){ //mrange
			int64_t r3 = (___c_s_4___l2 + 1); //inline variable
			int64_t ___o_l5 = 1;
			for (int ___c_h3___l1 = 0; ___c_h3___l1 < ___c_h3->cur_size; ___c_h3___l1++) {
				int64_t ___c_h3___l2 = getitem(___c_h3, ___c_h3___l1).i;
				if ((!((int) r3 % (int) ___c_h3___l2))) {___o_l5 = 0; goto ___lbl3;} //none
			}
___lbl3:
			Quant ___q_p21 = {.i=r3};
			if (___o_l5) {append(___c_h3, ___q_p21);}
		}
		for (int ___c_h3___l1 = 0; ___c_h3___l1 < ___c_h3->cur_size; ___c_h3___l1++) {
			int64_t ___c_h3___l2 = getitem(___c_h3, ___c_h3___l1).i;
			int64_t all_primes = ___c_h3___l2; //inline variable
				int64_t expon = 0;
			for (expon = 0; 1; expon++) {
				if (((int) x % (int) (pow(___c_h3___l2, expon)))) goto ___lbl4; //first
			}
___lbl4:
			if (1) {___o_l4 *= expon;} //product
		}
		destroy_list(___c_h3);
		return ___o_l4;
	}
	printf("%d\n", number_of_divisors(840));
		int64_t i = 0;
	for (i = 0; 1; i++) {
		if ((number_of_divisors(i) > 32)) goto ___lbl5; //first
	}
___lbl5:
	printf("%d\n", i);
	typedef struct {
		double x;
		double y;
	} Vec2;
		double magnitude(Vec2* v) {
		return sqrt(((pow(v->x, 2)) + (pow(v->y, 2))));
	}
	Vec2 ___s_p___s_p0 = {.x = 8, .y = 15};
	Vec2* ___s_p___s_p0_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p0_1, &___s_p___s_p0, sizeof(Vec2));
	printf("%f\n", magnitude(___s_p___s_p0_1));
	typedef struct {
		Vec2* v;
		int64_t d;
		double f;
	} ComplexContainer;
	Vec2 ___s_p___s_p2 = {.x = 17, .y = 4};
	Vec2* ___s_p___s_p2_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p2_1, &___s_p___s_p2, sizeof(Vec2));
	ComplexContainer ___s_p___s_p1 = {.v = ___s_p___s_p2_1, .d = 5, .f = (-17.4)};
	ComplexContainer* ___s_p___s_p1_1 = malloc(sizeof(ComplexContainer));
	memcpy(___s_p___s_p1_1, &___s_p___s_p1, sizeof(ComplexContainer));
	ComplexContainer* cc = ___s_p___s_p1_1;
	printf("ComplexContainer(v: Vec2(x: %f, y: %f), d: %d, f: %f)\n", ((Vec2*) ((ComplexContainer*) cc)->v)->x, ((Vec2*) ((ComplexContainer*) cc)->v)->y, ((ComplexContainer*) cc)->d, ((ComplexContainer*) cc)->f);
	dict* asd___d = make_dict();
			Vec2* asd(int64_t i) {
	Quant ___q_p22 = {.i=i};
		if (dict_has(asd___d, ___q_p22)) {
					return dict_get(asd___d, ___q_p22).s;
		} else {
	Vec2 ___s_p___s_p3 = {.x = (2 * i), .y = (pow(i, 2))};
	Vec2* ___s_p___s_p3_1 = malloc(sizeof(Vec2));
	memcpy(___s_p___s_p3_1, &___s_p___s_p3, sizeof(Vec2));
			Vec2* ___outp = ___s_p___s_p3_1;
			Vec2* ___c_p0 = malloc(sizeof(Vec2));
			memcpy(___c_p0, ___outp, sizeof(Vec2));
			Quant ___q_p23 = {.s=___c_p0};
			free(___s_p___s_p3_1);
			return dict_set(asd___d, ___q_p22, ___q_p23).s;
		}
	}
		Vec2* asd___l2 = 0;
	for (int asd___l2___l1 = 0; 1; asd___l2___l1++) {
		asd___l2 = asd(asd___l2___l1);
		if ((magnitude(asd___l2) > 30)) goto ___lbl6; //first
	}
___lbl6:
	printf("Vec2(x: %f, y: %f)\n", ((Vec2*) asd___l2)->x, ((Vec2*) asd___l2)->y);
		Vec2* to_vec(int64_t x) {
		Vec2 ___s_p___s_p4 = {.x = x, .y = x};
		Vec2* ___s_p___s_p4_1 = malloc(sizeof(Vec2));
		memcpy(___s_p___s_p4_1, &___s_p___s_p4, sizeof(Vec2));
		Vec2* ___c_p1 = malloc(sizeof(Vec2));
		memcpy(___c_p1, ___s_p___s_p4_1, sizeof(Vec2));
		free(___s_p___s_p4_1);
		return ___c_p1;
	}
	printf("Vec2(x: %f, y: %f)\n", ((Vec2*) to_vec(8))->x, ((Vec2*) to_vec(8))->y);
		list* ___p_s9 = make_list();
	for (int ___c_s_5 = 0; ___c_s_5 < 5; ___c_s_5++){
		double ___c_s_6___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1); //random
		Quant ___q_p24 = {.f=___c_s_6___l2};
		append(___p_s9, ___q_p24); //print
	}
	printf("{");
	for (int ___p_s9_1 = 0; ___p_s9_1 < ___p_s9->cur_size; ___p_s9_1++) {
		printf("%f", getitem(___p_s9, ___p_s9_1).f);
		if (___p_s9_1 != ___p_s9->cur_size-1) printf(", ");
	}
	printf("}\n");
	destroy_list(___p_s9);
			list* ran_vecs = make_list();
	for (int ___c_s_7 = 0; ___c_s_7 < 5000; ___c_s_7++){
		double ___c_s_8___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1); //random
		for (int ___c_s_9 = 0; ___c_s_9 < 500; ___c_s_9++){
			double ___c_s_10___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1); //random
	Vec2 ___s_p___s_p5 = {.x = ___c_s_8___l2, .y = ___c_s_10___l2};
			Vec2* ___s_p___s_p5_1 = malloc(sizeof(Vec2));
			memcpy(___s_p___s_p5_1, &___s_p___s_p5, sizeof(Vec2));
			Vec2* ___c_p2 = malloc(sizeof(Vec2));
			memcpy(___c_p2, ___s_p___s_p5_1, sizeof(Vec2));
			Quant ___q_p25 = {.s=___c_p2};
			append(ran_vecs, ___q_p25);
		free(___s_p___s_p5_1);
		}
	}
	int ___o_l6_counter = 0;
	int64_t ___o_l6 = 0;
	for (int ran_vecs___l1 = 0; ran_vecs___l1 < ran_vecs->cur_size; ran_vecs___l1++) {
		Vec2* ran_vecs___l2 = getitem(ran_vecs, ran_vecs___l1).s;
		___o_l6 += (((pow(ran_vecs___l2->x, 2)) + (pow(ran_vecs___l2->y, 2))) < 1); ___o_l6_counter++; //average
	}
	printf("%f\n", ((float) ___o_l6 / ___o_l6_counter * 4));
	destroy_list(r1);
	destroy_list(___c_h0);
	destroy_list(r2);
	destroy_list(primes);
	destroy_list(___c_h1);
	destroy_list(___c_h2);
	destroy_dict(fibs___d);
	free(___s_p___s_p0_1);
	free(___s_p___s_p2_1);
	free(___s_p___s_p1_1);
	for (int asd___d___l1 = 0; asd___d___l1 < asd___d->cur_size; asd___d___l1++) {
		free(asd___d->pairs[asd___d___l1].value.s);
	}
	destroy_dict(asd___d);
	for (int ran_vecs___l1 = 0; ran_vecs___l1 < ran_vecs->cur_size; ran_vecs___l1++) {
		free(getitem(ran_vecs, ran_vecs___l1).s);
	}
	destroy_list(ran_vecs);
}
