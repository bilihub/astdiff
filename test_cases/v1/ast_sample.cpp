#include <iostream>
#include <vector>

// 1. 基本算术运算与顺序 (测试语句乱序免疫)
int check_ast(int a, int b) {
  int c = a + b;
  int d = a * b;
  return c;
}

// 2. 控制流: 纯粹的排版区别 (测试是否识别为无实质 AST 变动)
bool is_valid_user(int age, bool has_license) {
  if (age >= 18) {
    if (has_license) {
      return true;
    } else {
      return false;
    }
  }
  return false;
}

// 3. 循环结构: 修改边界条件 (测试 AST 能否捕获细微到表达式的变更)
int sum_array(const std::vector<int> &arr) {
  int sum = 0;
  for (int i = 0; i < arr.size(); i++) {
    sum += arr[i];
  }
  return sum;
}

// 4. 函数签名与参数类型 (测试跨类型的修改)
float calculate_discount(float price, float discount_rate) {
  return price * (1.0f - discount_rate);
}

// 5. 变量重命名与重构 (测试标示符更改检测)
void process_data() {
  int temp_val = 100;
  int res = temp_val * 2;
  std::cout << res << std::endl;
}

// 6. 无逻辑关联的简单语句乱序 (测试真正的 AST 重排免疫)
void reorder_test() {
  int a = 1;
  int b = 2;
  int c = 3;
}

// 7. 类与方法 (测试类方法的 AST 识别)
class Calculator {
public:
  int add(int a, int b) { return a + b; }

  int subtract(int a, int b) { return a - b; }
};

// 8. 模板函数 (测试模板声明的 AST 识别与变化)
template <typename T> T find_max(T a, T b) {
  if (a > b) {
    return a;
  }
  return b;
}
