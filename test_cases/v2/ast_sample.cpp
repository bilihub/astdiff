#include <iostream>
#include <vector>

// 1. 基本算术运算与顺序 (测试语句乱序免疫)
// 预期: AST 侦测到操作符被修改，但不应该像文本一样报大面积的删除新增
int check_ast(int a, int b) {
  // 增加了一堆注释和空行干扰

  int d = a / b; // AST Mod: changed '*' to '/'
  int c = a + b;

  return c;
}

// 2. 控制流: 纯粹的排版区别 (测试是否识别为无实质 AST 变动)
// 预期: 即使格式被严重打乱，AST Diff 返回的 ast_nodes_modified 应该为 0
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
// 预期: AST 能够精准检测到 '<' 变成了 '<='
int sum_array(const std::vector<int> &arr) {
  int sum = 0;
  for (int i = 0; i <= arr.size(); i++) { // Changed < to <=
    sum += arr[i];
  }
  return sum;
}

// 4. 函数签名与参数类型 (测试跨类型的修改)
// 预期: 因为参数类型变成了 double，它被视为一个新的函数（因为签名变了）或修改
double calculate_discount(double price, double discount_rate) {
  return price * (1.0 - discount_rate); // changed float to double
}

// 5. 变量重命名与重构 (测试标示符更改检测)
// 预期: AST 会检测到 identifier 节点文本本身的变更
void process_data() {
  int initial_value = 100;        // changed temp_val to initial_value
  int result = initial_value * 2; // changed res to result
  std::cout << result << std::endl;
}

// 6. 无逻辑关联的简单语句乱序 (测试真正的 AST 重排免疫)
// 预期:
// 顺序打乱，但是所有的操作树都能在旧序列中找到完美等价节点。应修改为0被忽略。
void reorder_test() {
  int c = 3;
  int a = 1;
  int b = 2;
}

// 7. 类与方法 (测试类方法的 AST 识别)
// 测试: 逻辑变更与内部排版调整
class Calculator {
public:
  int add(int a, int b) {
    return b + a; // Mod: changed order of operands
  }

  int subtract(int a, int b) { return a - b; }
};

// 8. 模板函数 (测试模板声明的 AST 识别与变化)
// 测试: 模板标识符和内部操作符的变化
template <typename T> T find_max(T a, T b) {
  if (a >= b) { // Mod: changed > to >=
    return a;
  }
  return b;
}
