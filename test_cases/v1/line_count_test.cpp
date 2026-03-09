// 精确行数测试文件 v1
// 总共 30 行

// 函数A: 不变 (3行, L4-L6)
int func_a() { return 1; }

// 函数B: 修改1行常量 (3行, L9-L11)
int func_b() { return 100; }

// 函数C: 将被删除 (3行, L14-L16)
int func_c() { return 999; }

// 函数D: 修改2行 (5行, L19-L23)
int func_d(int x) {
  int a = x + 1;
  int b = x + 2;
  return a + b;
}

// 全局变量E: 修改值 (1行, L26)
int g_config = 10;

// 全局变量F: 不变 (1行, L29)
int g_version = 1;
