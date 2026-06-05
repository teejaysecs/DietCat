#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    // If the web app forgot to pass an age, stop early
    if (argc < 2) {
        printf("No Age Provided");
        return 1;
    }

    // This converts the age sent by the web app into a usable number
    int age = atoi(argv[1]);

    // Your original checking logic
    if (age >= 0 && age <= 12) {
        printf("Child");
    } else if (age >= 13 && age <= 19) {
        printf("Teenager");
    } else if (age >= 20 && age <= 50) {
        printf("Youth");
    } else if (age > 50 && age <= 60) {
        printf("Senior Citizen");
    } else {
        printf("Out of range");
    }

    return 0;
}
