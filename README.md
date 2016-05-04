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


| 符号类型	| 说明                    |
|-----------|------------------------|
|A	| 该符号的值是绝对的，在以后的链接过程中，不允许进行改变。这样的符号值，常常出现在中断向量表中，例如用符号来表示各个中断向量函数在中断向量表中的位置。|
|B	|该符号的值出现在非初始化数据段(bss)中。例如，在一个文件中定义全局static int test。则该符号test的类型为b，位于bss section中。其值表示该符号在bss段中的偏移。一般而言，bss段分配于RAM中 |
| C	|该符号为common。common symbol是未初始话数据段。该符号没有包含于一个普通section中。只有在链接过程中才进行分配。符号的值表示该符号需要的字节数。例如在一个c文件中，定义int test，并且该符号在别的地方会被引用，则该符号类型即为C。否则其类型为B。|
| D	| 该符号位于初始话数据段中。一般来说，分配到data section中。例如定义全局int baud_table[5] = {9600, 19200, 38400, 57600, 115200}，则会分配于初始化数据段中。|
| G	| 该符号也位于初始化数据段中。主要用于small object提高访问small data object的一种方式。|
| I	| 该符号是对另一个符号的间接引用。 |
| N | 该符号是一个debugging符号。|
| R	| 该符号位于只读数据区。例如定义全局const int test[] = {123, 123};则test就是一个只读数据区的符号。注意在cygwin下如果使用gcc直接编译成MZ格式时，源文件中的test对应_test，并且其符号类型为D，即初始化数据段中。但是如果使用m6812-elf-gcc这样的交叉编译工具，源文件中的test对应目标文件的test,即没有添加下划线，并且其符号类型为R。一般而言，位于rodata section。值得注意的是，如果在一个函数中定义const char *test = “abc”, const char test_int = 3。使用nm都不会得到符号信息，但是字符串“abc”分配于只读存储器中，test在rodata section中，大小为4。|
| S	| 符号位于非初始化数据区，用于small object。|
| T	| 该符号位于代码区text section。|
| U	| 该符号在当前文件中是未定义的，即该符号的定义在别的文件中。例如，当前文件调用另一个文件中定义的函数，在这个被调用的函数在当前就是未定义的；但是在定义它的文件中类型是T。但是对于全局变量来说，在定义它的文件中，其符号类型为C，在使用它的文件中，其类型为U。|
| V	| 该符号是一个weak object。|
| W	| The symbol is a weak symbol that has not been specifically tagged as a weak object symbol.|
| -	| 该符号是a.out格式文件中的stabs symbol。|
| ?	| 该符号类型没有定义 |



## 使用方法

1. 安装gcc工具链，且在 PATH 路径里；
2. Graphviz工具，且在 PATH 路径里；
3. 运行：
	nm *.o > obj_symb.txt
	python obj-symb-ref.py obj_symb.txt out_dir

4. 输出图片的例子：

![图片1](https://github.com/randomatom/obj-symb-ref/raw/master/image/exam1.png)
![图片2](https://github.com/randomatom/obj-symb-ref/raw/master/image/exam_all.png)

