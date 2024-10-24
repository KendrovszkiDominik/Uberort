#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define INITIAL_CAPACITY 16
#define US_SIZE 262144

int cur_set_i_ind = 0;

struct Cache;

union Quant{
    int64_t i;
    double f;
    struct Cache* c;
    void* s;
};

typedef struct {
    uint8_t allocated; // 0-not allocated, 1-allocated, 2-freed up
    union Quant element;
    uint16_t rev_ind; // index in the dy_set_i
    uint8_t is_ptr; // 0-not pointer, 1-void, 2-cache
} si_e;

si_e universal_set[US_SIZE]; // 18-bit hash array containing integers

// 18-bit hash for integers
uint hash_int(int a, int sp_index) {
    return (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
}

uint64_t float_to_int_bits(double f) {
    union {
        double f;
        uint64_t i;
    } u;
    u.f = f;
    return u.i & ((1<<16)-1);
}

// 18-bit hash for floats
uint hash_float(double f, int sp_index) {
    uint64_t a = float_to_int_bits(f);
    return (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
}

// 18-bit hash for structs
uint hash_struct(int64_t* f, int sp_index, int size) {
    int outp = 0;
    for (int i = 0; i<size/8; i++) {
        int64_t a = f[i] & ((1<<16)-1);
        outp += (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
        outp = outp*3 + ((outp%63) << 3);
    }
    return outp % US_SIZE;
}

typedef struct {
    int* elements;   // array to hold element indices
    int size;        // number of elements in the set
    int capacity;    // current allocated capacity
    int ind;         // index of the set (for better hash)
} dy_set_i;

dy_set_i* create_set_i() {
    dy_set_i *self = malloc(sizeof(dy_set_i));
    self->elements = malloc(INITIAL_CAPACITY * sizeof(int64_t));
    self->size = 0;
    self->capacity = INITIAL_CAPACITY;
    self->ind = cur_set_i_ind++;
    return self;
}

typedef struct Cache {
    union Quant key;
    union Quant element;
} Cache;

int is_cached_i(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return 1;
            }
        }
    }
}

int64_t get_cache_i(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.i;
            }
        }
    }
}

int64_t cache_i(int item, int value, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].element.c->element.i = value;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            return value;
        }
    }
}

double get_cache_f(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.f;
            }
        }
    }
}

double cache_f(int item, double value, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].element.c->element.f = value;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            return value;
        }
    }
}

void* get_cache_s(int item, int ind, int size) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
            universal_set[i%US_SIZE].rev_ind == 65535 &&
            universal_set[i%US_SIZE].is_ptr == 2) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.s;
            }
        }
    }
}

void* cache_s(int item, void* value, int ind, int size) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->element.s = malloc(size);
            if (universal_set[i%US_SIZE].element.s == NULL) {
                fprintf(stderr, "Error: Memory allocation failed\n");
                exit(1);
            }
            memcpy(universal_set[i%US_SIZE].element.c->element.s, value, size);
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            universal_set[i%US_SIZE].is_ptr = 2;
            return value;
        }
    }
}

int contains_i(dy_set_i* self, int item) {
    for (int i = hash_int(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.i == item) { // no false matches
                return 1;
            }
        }
    }
}

void append_i(dy_set_i* self, int item) {
    if (!contains_i(self, item)) {
        for (int i = hash_int(item, self->ind); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.i = item;
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 0;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(int64_t));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_i(dy_set_i* self, int item) {
    for (int i = hash_int(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.i == item) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind =
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void print_set_i(dy_set_i* self) {
    printf("{");
    for (int i = 0; i < self->size; i++) {
        printf("%d", universal_set[self->elements[i]].element.i);
        if (i != self->size-1) {
            printf(", ");
        }
    }
    printf("}\n");
}

void array_to_set_i(dy_set_i* self, int64_t* arr, int size) {
    for (int i = 0; i < size; i++) {
        append_i(self, arr[i]);
    }
}

dy_set_i* add_set_i(dy_set_i* self, dy_set_i* other) {
    dy_set_i* outp = create_set_i();
    for (int i = 0; i < self->size; i++) {
        for (int j = 0; j < other->size; j++) {
            append_i(outp, universal_set[self->elements[i]].element.i +
                    universal_set[other->elements[j]].element.i);
        }
    }
    return outp;
}

void clear_set_i(dy_set_i* self) {
    for (;self->size;) {
        remove_i(self, universal_set[self->elements[0]].element.i);
    }
}

dy_set_i* create_set_f() {
    dy_set_i *self = malloc(sizeof(dy_set_i));
    self->elements = malloc(INITIAL_CAPACITY * sizeof(double));
    self->size = 0;
    self->capacity = INITIAL_CAPACITY;
    self->ind = cur_set_i_ind++;
    return self;
}

int contains_f(dy_set_i* self, double item) {
    for (int i = hash_float(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.f == item) { // no false matches
                return 1;
            }
        }
    }
}

void append_f(dy_set_i* self, double item) {
    if (!contains_f(self, item)) {
        for (int i = hash_float(item, self->ind); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.f = item;
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 0;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(double));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_f(dy_set_i* self, double item) {
    for (int i = hash_float(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.f == item) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind =
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void print_set_f(dy_set_i* self) {
    printf("{");
    for (int i = 0; i < self->size; i++) {
        printf("%f", universal_set[self->elements[i]].element.f);
        if (i != self->size-1) {
            printf(", ");
        }
    }
    printf("}\n");
}

void array_to_set_f(dy_set_i* self, double* arr, int size) {
    for (int i = 0; i < size; i++) {
        append_f(self, arr[i]);
    }
}

void clear_set_f(dy_set_i* self) {
    for (;self->size;) {
        remove_f(self, universal_set[self->elements[0]].element.f);
    }
}

int contains_s(dy_set_i* self, void* item, int size) {
    for (int i = hash_struct(item, self->ind, size); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1 && universal_set[i%US_SIZE].is_ptr == 1) {
            if (!memcmp(universal_set[i%US_SIZE].element.s, item, size)) { // no false matches
                return 1;
            }
        }
    }
}

void append_s(dy_set_i* self, void* item, int size) {
    if (!contains_s(self, item, size)) {
        for (int i = hash_struct(item, self->ind, size); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.s = malloc(size);
                if (universal_set[i%US_SIZE].element.s == NULL) {
                    fprintf(stderr, "Error: Memory allocation failed\n");
                    exit(1);
                }
                memcpy(universal_set[i%US_SIZE].element.s, item, size);
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 1;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(double));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_s(dy_set_i* self, void* item, int size) {
    for (int i = hash_struct(item, self->ind, size); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (!memcmp(universal_set[i%US_SIZE].element.s, item, size)) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind =
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void clear_set_s(dy_set_i* self, int size) {
    for (;self->size;) {
        remove_s(self, universal_set[self->elements[0]].element.s, size);
    }
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

double gauss_cd(double x) {
    return 0.5 * (1 + erf(x / sqrt(2)));
}


int main() {
        srand ( time(NULL) );
        int64_t ia = 4;
        double fb = 7.0;
        printf("%f\n", (ia + fb));
        dy_set_i* sia = create_set_i();
        int64_t ___b_a0[4] = {1, 3, 5, 9};
        array_to_set_i(sia, ___b_a0, 4);
        dy_set_i* sib = create_set_i();
        int64_t ___b_a1[3] = {1, 9, 40};
        array_to_set_i(sib, ___b_a1, 3);
                        dy_set_i* ___p_s0 = create_set_i();
        for (int sia___l1 = 0; sia___l1 < sia->size; sia___l1++) {
                int64_t sia___l2 = universal_set[sia->elements[sia___l1]].element.i;
                for (int sib___l1 = 0; sib___l1 < sib->size; sib___l1++) {
                        int64_t sib___l2 = universal_set[sib->elements[sib___l1]].element.i;
                        append_i(___p_s0, (sia___l2 + sib___l2));
                }
        }
        print_set_i(___p_s0);
        clear_set_i(___p_s0);
                dy_set_i* ___p_s1 = create_set_f();
        for (int sia___l1 = 0; sia___l1 < sia->size; sia___l1++) {
                int64_t sia___l2 = universal_set[sia->elements[sia___l1]].element.i;
                append_f(___p_s1, sin(sia___l2));
        }
        print_set_f(___p_s1);
        clear_set_f(___p_s1);
                dy_set_i* ___p_s2 = create_set_i();
        for (int sia___l1 = 0; sia___l1 < sia->size; sia___l1++) {
                int64_t sia___l2 = universal_set[sia->elements[sia___l1]].element.i;
                append_i(___p_s2, (sia___l2 + sia___l2));
        }
        print_set_i(___p_s2);
        clear_set_i(___p_s2);
                dy_set_i* ___p_s3 = create_set_f();
        for (int sia___l1 = 0; sia___l1 < sia->size; sia___l1++) {
                int64_t sia___l2 = universal_set[sia->elements[sia___l1]].element.i;
                append_f(___p_s3, (sia___l2 + sin(sia___l2)));
        }
        print_set_f(___p_s3);
        clear_set_f(___p_s3);
        int64_t a = 10;
        int64_t b = 15;
                dy_set_i* r1 = create_set_i();
        for (int ___c_s_0___l2 = 1; ___c_s_0___l2 <= (a < b ? a : b); ___c_s_0___l2++){
                append_i(r1, ___c_s_0___l2);
        }
        int64_t ___o_l1 = 0;
        int64_t ___o_l0 = 0;
        dy_set_i* print = create_set_i();
        for (int r1___l1 = 0; r1___l1 < r1->size; r1___l1++) {
                int64_t r1___l2 = universal_set[r1->elements[r1___l1]].element.i;
                if (((!((int) a % (int) r1___l2)) && (!((int) b % (int) r1___l2))) && (___o_l1 < r1___l2)) {___o_l0 = r1___l2; ___o_l1 = r1___l2;}
        }
        printf("%d\n", ((int) (a * b) / (int) ___o_l0));
                dy_set_i* ___p_s4 = create_set_i();
        dy_set_i* ___c_h0 = create_set_i();
        for (int r1___l1 = 0; r1___l1 < r1->size; r1___l1++) {
                int64_t r1___l2 = universal_set[r1->elements[r1___l1]].element.i;
                if (((!((int) a % (int) r1___l2)) && (!((int) b % (int) r1___l2)))) {append_i(___c_h0, r1___l2);}
        }
        for (int ___c_h0___l1 = 0; ___c_h0___l1 < ___c_h0->size; ___c_h0___l1++) {
                int64_t ___c_h0___l2 = universal_set[___c_h0->elements[___c_h0___l1]].element.i;
                append_i(___p_s4, ___c_h0___l2);
        }
        print_set_i(___p_s4);
        clear_set_i(___p_s4);
                dy_set_i* r2 = create_set_i();
        for (int ___c_s_1___l2 = 1; ___c_s_1___l2 <= 50; ___c_s_1___l2++){
                append_i(r2, (___c_s_1___l2 + 1));
        }
        dy_set_i* primes = create_set_i();
        for (int r2___l1 = 0; r2___l1 < r2->size; r2___l1++) {
                int64_t r2___l2 = universal_set[r2->elements[r2___l1]].element.i;
                int64_t ___o_l2 = 1;
                for (int primes___l1 = 0; primes___l1 < primes->size; primes___l1++) {
                        int64_t primes___l2 = universal_set[primes->elements[primes___l1]].element.i;
                        if ((!((int) r2___l2 % (int) primes___l2))) {___o_l2 = 0; goto ___lbl0;}
                }
___lbl0:
                if (___o_l2) {append_i(primes, r2___l2);}
        }
                dy_set_i* ___p_s5 = create_set_i();
        for (int primes___l1 = 0; primes___l1 < primes->size; primes___l1++) {
                int64_t primes___l2 = universal_set[primes->elements[primes___l1]].element.i;
                append_i(___p_s5, primes___l2);
        }
        print_set_i(___p_s5);
        clear_set_i(___p_s5);
                dy_set_i* ___p_s6 = create_set_i();
        dy_set_i* ___c_h1 = create_set_i();
                int64_t ri;
        for (int ___c_s_2___l2 = 0; ___c_s_2___l2 < 60; ___c_s_2___l2++){
                ri = ___c_s_2___l2;
                if (((!((int) ri % (int) 3)) && ((int) ri % (int) 7))) {append_i(___c_h1, ri);}
        }
        for (int ___c_h1___l1 = 0; ___c_h1___l1 < ___c_h1->size; ___c_h1___l1++) {
                int64_t ___c_h1___l2 = universal_set[___c_h1->elements[___c_h1___l1]].element.i;
                append_i(___p_s6, ___c_h1___l2);
        }
        print_set_i(___p_s6);
        clear_set_i(___p_s6);
                dy_set_i* ___p_s7 = create_set_i();
                int64_t rec_inline;
        dy_set_i* ___c_h2 = create_set_i();
                int64_t range_inline;
        for (int ___c_s_3___l2 = 1; ___c_s_3___l2 <= 50; ___c_s_3___l2++){
                range_inline = (___c_s_3___l2 + 1);
                int64_t ___o_l3 = 1;
                for (int ___c_h2___l1 = 0; ___c_h2___l1 < ___c_h2->size; ___c_h2___l1++) {
                        int64_t ___c_h2___l2 = universal_set[___c_h2->elements[___c_h2___l1]].element.i;
                        if ((!((int) range_inline % (int) ___c_h2___l2))) {___o_l3 = 0; goto ___lbl1;}
                }
___lbl1:
                if (___o_l3) {append_i(___c_h2, range_inline);}
        }
        for (int ___c_h2___l1 = 0; ___c_h2___l1 < ___c_h2->size; ___c_h2___l1++) {
                int64_t ___c_h2___l2 = universal_set[___c_h2->elements[___c_h2___l1]].element.i;
                rec_inline = ___c_h2___l2;
                append_i(___p_s7, ___c_h2___l2);
        }
        print_set_i(___p_s7);
        clear_set_i(___p_s7);
        int64_t fibs(int64_t i, int ___ind) {
                if (is_cached_i(i, ___ind)) {
                        return get_cache_i(i, ___ind);
                } else {
                        int64_t ___outp = (fibs((i - 2), 0) + fibs((i - 1), 0));
                        return cache_i(i, ___outp, ___ind);
                }
        }
        cache_i(0, 1, 0);
        cache_i(1, 1, 0);
        for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("%d, ", fibs(___l_var, 0));
        printf("%d...\n", fibs(16, 0));
        printf("%d\n", fibs(5, 0));
                int64_t fibs___l2 = 0;
        for (int fibs___l2___l1 = 0; 1; fibs___l2___l1++) {
                fibs___l2 = fibs(fibs___l2___l1, 0);
                if ((fibs___l2 > 9000)) goto ___lbl2;
        }
___lbl2:
        printf("%d\n", fibs___l2);
        double square(double x) {
                return (pow(x, 2));
        }
        printf("%f\n", square(7.3));
                dy_set_i* ___p_s8 = create_set_f();
        for (int sia___l1 = 0; sia___l1 < sia->size; sia___l1++) {
                int64_t sia___l2 = universal_set[sia->elements[sia___l1]].element.i;
                append_f(___p_s8, square(sia___l2));
        }
        print_set_f(___p_s8);
        clear_set_f(___p_s8);
        int64_t number_of_divisors(int64_t x) {
                int64_t ___o_l4 = 1;
                        int64_t all_primes;
                dy_set_i* ___c_h3 = create_set_i();
                        int64_t r2;
                for (int ___c_s_4___l2 = 1; ___c_s_4___l2 <= x; ___c_s_4___l2++){
                        r2 = (___c_s_4___l2 + 1);
                        int64_t ___o_l5 = 1;
                        for (int ___c_h3___l1 = 0; ___c_h3___l1 < ___c_h3->size; ___c_h3___l1++) {
                                int64_t ___c_h3___l2 = universal_set[___c_h3->elements[___c_h3___l1]].element.i;
                                if ((!((int) r2 % (int) ___c_h3___l2))) {___o_l5 = 0; goto ___lbl3;}
                        }
___lbl3:
                        if (___o_l5) {append_i(___c_h3, r2);}
                }
                for (int ___c_h3___l1 = 0; ___c_h3___l1 < ___c_h3->size; ___c_h3___l1++) {
                        int64_t ___c_h3___l2 = universal_set[___c_h3->elements[___c_h3___l1]].element.i;
                        all_primes = ___c_h3___l2;
                        dy_set_i* number_of_divisors = create_set_i();
                                int64_t expon = 0;
                        for (expon = 0; 1; expon++) {
                                if (((int) x % (int) (pow(___c_h3___l2, expon)))) goto ___lbl4;
                        }
___lbl4:
                        if (1) {___o_l4 *= expon;}
                }
                return ___o_l4;
        }
        printf("%d\n", number_of_divisors(840));
                int64_t i = 0;
        for (i = 0; 1; i++) {
                if ((number_of_divisors(i) > 32)) goto ___lbl5;
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
        printf("ComplexContainer(v: Vec2(x: %f, y: %f), d: %d, f: %f)\n", cc->v->x, cc->v->y, cc->d, cc->f);
        Vec2* asd(int64_t i, int ___ind) {
                if (is_cached_i(i, ___ind)) {
                        return get_cache_s(i, ___ind, sizeof(Vec2));
                } else {
        Vec2 ___s_p___s_p3 = {.x = (2 * i), .y = (pow(i, 2))};
        Vec2* ___s_p___s_p3_1 = malloc(sizeof(Vec2));
        memcpy(___s_p___s_p3_1, &___s_p___s_p3, sizeof(Vec2));
                        Vec2* ___outp = ___s_p___s_p3_1;
                        return cache_s(i, ___outp, ___ind, sizeof(Vec2));
                }
        }
                Vec2* asd___l2 = 0;
        for (int asd___l2___l1 = 0; 1; asd___l2___l1++) {
                asd___l2 = asd(asd___l2___l1, 1);
                if ((magnitude(asd___l2) > 30)) goto ___lbl6;
        }
___lbl6:
        printf("Vec2(x: %f, y: %f)\n", asd___l2->x, asd___l2->y);
                dy_set_i* ___p_s9 = create_set_f();
        for (int ___c_s_5 = 0; ___c_s_5 < 5; ___c_s_5++){
                double ___c_s_6___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1);
                append_f(___p_s9, ___c_s_6___l2);
        }
        print_set_f(___p_s9);
        clear_set_f(___p_s9);
                        dy_set_i* ran_vecs = create_set_i();
        for (int ___c_s_7 = 0; ___c_s_7 < 50; ___c_s_7++){
                double ___c_s_8___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1);
                for (int ___c_s_9 = 0; ___c_s_9 < 50; ___c_s_9++){
                        double ___c_s_10___l2 = ((1 - (-1)) * ((float)rand() / RAND_MAX)) + (-1);
        Vec2 ___s_p___s_p4 = {.x = ___c_s_8___l2, .y = ___c_s_10___l2};
                        Vec2* ___s_p___s_p4_1 = malloc(sizeof(Vec2));
                        memcpy(___s_p___s_p4_1, &___s_p___s_p4, sizeof(Vec2));
                        append_s(ran_vecs, ___s_p___s_p4_1, sizeof(Vec2));
                }
        }
        int ___o_l6_counter = 0;
        int64_t ___o_l6 = 0;
        for (int ran_vecs___l1 = 0; ran_vecs___l1 < ran_vecs->size; ran_vecs___l1++) {
                Vec2* ran_vecs___l2 = universal_set[ran_vecs->elements[ran_vecs___l1]].element.s;
                ___o_l6 += (((pow(ran_vecs___l2->x, 2)) + (pow(ran_vecs___l2->y, 2))) < 1); ___o_l6_counter++;
        }
        printf("%f\n", ((float) ___o_l6 / ___o_l6_counter * 4));
}

