#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char* argv[]) {
    int start = 0;
    int end = 5000;

    // Accept optional command-line arguments: program <start> <end>
    if (argc >= 2) start = atoi(argv[1]);
    if (argc >= 3) end = atoi(argv[2]);

    if (start > end) {
        cout << "Error: start (" << start << ") cannot be greater than end (" << end << ")." << endl;
        return 1;
    }

    for (int i = start; i <= end; i++) {
        cout << "Your Phone has been hacked!" << endl;
    }

    return 0;
}