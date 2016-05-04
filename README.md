# obj-symb-ref

利用obj文件的信息，生成模块之间的交叉引用关系，便于对整个项目进行分析。

## 项目缘起
以前在做一些嵌入式的项目的时候，常常需要 port第三方的库。
这些库的文档不一定非常全面，如何快速的对这个库的代码进行分析，成为一个问题。
通常会用sourceinsight进行阅读和分析，但对于模块之间的总体的依赖关系，分析起来总是不方面。
由于C语言的宏的特性，对其进行语法解析，分析模块之间的依赖关系是极其麻烦的。
于是，想到用 obj 文件中的符号信息，进行分析。

## 思路

### obj文件中的符号

在一个文件的编译之后，会生成obj文件。obj文件里，包含各种不同的符号。
这些符号，大体可以分为两类：

- **内部定义** ：可以认为是 「函数的定义」，通常是 用 tags:T 表示
- **在外部定义** ：模块需要用到的「外部符号」，通常用 tags:U 表示

比如 obj1 定义了 sub-fun() ；
obj2 定义 control-fun() ，而且内部调用 obj1的sub_fun()
这样，obj2 就 引用的 obj1。记做：obj2 --> obj1


符号的具体的解释可以看 
> man nm

## 使用方法

1. 安装gcc工具链，且在 PATH 路径里；
2. Graphviz工具，且在 PATH 路径里；
3. 运行：

> 
	nm *.o > obj_symb.txt
	python obj-symb-ref.py obj_symb.txt out_dir

4. 输出

！[图片1](https://github.com/randomatom/obj-symb-ref/raw/master/image/exam_all.png)
！[图片2](https://github.com/randomatom/obj-symb-ref/raw/master/image/exam1.png)





