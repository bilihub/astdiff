#include <iostream>
#include <string>

class User {
public:
  User(int id, const std::string &name) : id_(id), name_(name) {}

  // Modified printInfo to include formatting changes
  void printInfo() const {
    std::cout << "[V2 Format] User ID: " << id_ << " | Name: " << name_
              << std::endl;
  }

  int getId() const { return id_; }

  // Added a new function in V2
  std::string getName() const { return name_; }

private:
  int id_;
  std::string name_; // Kept same
};

// Modified calculateTotal logic
int calculateTotal(int a, int b) {
  int total = a + b;
  if (total < 0)
    return 0; // Added business logic
  return total;
}

// Added new utility function
void logEvent(const std::string &evt) {
  std::cout << "LOG: " << evt << std::endl;
}

// obsoleteFunction has been deleted.
