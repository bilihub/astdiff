#include <iostream>
#include <string>

class User {
public:
  User(int id, const std::string &name) : id_(id), name_(name) {}

  void printInfo() const {
    std::cout << "User ID: " << id_ << ", Name: " << name_ << std::endl;
  }

  int getId() const { return id_; }

private:
  int id_;
  std::string name_;
};

int calculateTotal(int a, int b) { return a + b; }

void obsoleteFunction() {
  std::cout << "This function will be removed in V2." << std::endl;
}
