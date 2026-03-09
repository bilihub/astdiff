// 精确行数测试文件 v2
// 总共 31 行

// 函数A: 不变 (3行, L4-L6)
int func_a() { return 1; }

// 函数B: 修改1行常量 100->200 (3行, L9-L11)
int func_b() { return 200; }

// 函数C: 已删除 (不存在)

// 函数D: 修改2行 x+1->x*10, x+2->x*20 (5行, L16-L20)
int func_d(int x) {
  int a = x * 10;
  int b = x * 20;
  return a + b;
}

// 新增函数G (4行, L23-L26)
int func_g(int a, int b) {
  int sum = a + b;
  return sum;
}

// 全局变量E: 修改值 10->99 (1行, L29)
int g_config = 99;

// 全局变量F: 不变 (1行, L32)
int g_version = 1;
