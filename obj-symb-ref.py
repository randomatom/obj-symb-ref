#!/usr/bin/python
# coding=utf-8
'''
    Auth : @RandomAtom
    Data : 2010-12-20
    Brief: 生成.o文件之间的依赖关系 
	Log  :
		2011-3-20: 加入 'R','D'这些符号的判断
		2011-5-13: 加入 'B'这些符号的判断
	安装前提：
		1. 必须安装gcc工具链，且在 PATH 路径里；
		2. 安装Graphviz工具，且在 PATH 路径里；
	使用步骤:
		1. >> nm.exe *.o > obj_nm_symb.txt
		2. >> python obj-symb-ref.py obj_nm_symb.txt out_dir
'''

import sys
import os
import tempfile

class Digraph():
	def __init__(self, edge_list):
		self.edge_list = edge_list[:]  #[(caller, callee), ...]
		self.edge_list_with_group = []
		self.hight_light_obj = []
	def set_group(self, group):
		# group: [(group, [(obj, [children]), ...]), ...]
		if not group:
			self.edge_list_with_group = []
			return

		# check
		group_name_list = [g[0] for g in group]
		if len(set(group_name_list)) != len(group_name_list):
			raise 'dup group name!'
		obj_name_set = set()
		for g in group:
			for obj in g[1]:
				if obj[0] in obj_name_set:
					print obj[0]
				obj_name_set.add(obj[0])

		obj_dict = {}
		for g in group:
			for obj in g[1]:
				obj_dict[obj[0]] = g[0]
		edge_set_with_group = set()
		for edge in self.edge_list:
			edge_set_with_group.add( (obj_dict.getdefault(edge[0], dege[0]), \
				obj_dict.getdefault(edge[1], dege[1])) )
		self.edge_list_with_group = list(edge_set_with_group)

	def set_hight_light(self, obj_list):
		self.hight_light_obj = obj_list[:]

	def gen_graph(self, file_name):
		basename = os.path.splitext(file_name)[0]
		tmp_file = tempfile.mktemp()
		fd_graph = open(tmp_file, 'wb')
		fd_graph.write('digraph G {\n')
		
		edge_list = self.edge_list
		if self.edge_list_with_group : edge_list = self.edge_list_with_group
		for caller, callee in edge_list:
			fd_graph.write('\t\"{0}\" -> \"{1}\";\n'.format(caller, callee))
		for e in self.hight_light_obj:
				fd_graph.write('\t\"{0}\" [color = yellow, style = filled];\n'.format(e))
		fd_graph.write('}\n')
		fd_graph.close()
		
		cmd = r'dot -Tpng -o {0}.png {1}'.format(basename, tmp_file)
		print cmd
		os.popen(cmd)
		#os.remove(tmp_file)
		

class RefGraph():
	def __init__(self, symb_ref_list):
		self.symb_ref_list = []  # [(caller, callee, symb), ...]
		self.caller_dict = {}    # {caller:set(callee,...), ...}
		self.callee_dict = {}    # {callee:set(caller,...), ...}
		self.obj_list = []       # [obj_name, ...]
		self.init_data(symb_ref_list)
		
	def init_data(self, symb_ref_list):
		self.symb_ref_list = symb_ref_list[:]
		obj_set = set()
		for caller, callee, symb in self.symb_ref_list:
			if caller != callee:
				self.caller_dict.setdefault(caller, set()).add(callee)
				self.callee_dict.setdefault(callee, set()).add(caller)
			obj_set.add(caller)
			obj_set.add(callee)
		self.obj_list = sorted(list(obj_set))

	def get_obj_list(self):
		return self.obj_list[:]

	def print_ref_data(self, obj_list, fd):
		fd.write('\n {0} {1:^15} {2}\n'.format('*'*25, 'obj-module-type', '*'*25))
		for obj in sorted(obj_list):
			caller_flag = '------'
			callee_flag = '------'
			if obj in self.caller_dict:
				caller_flag = 'caller'
			if obj in self.callee_dict:
				callee_flag = 'callee'
			fd.write(' | {0:<35} | {1:^11} | {2:^11} |\n'.format(obj, caller_flag, callee_flag))
		
		fd.write('\n {0} {1:^15} {2}'.format('*'*39, '[ref relation]', '*'*39))
		fd.write('\n {0:^26} {1:^26} {2:^35}\n'.\
			format('% caller module %', '% callee module %', '% symbol %'))
		for ref in self.symb_ref_list:
			if ref[0] in obj_list or ref[1] in obj_list:
				fd.write(' | {0:<25} | {1:<25} | {2:<35} |\n'.format(ref[0], ref[1], ref[2]))

	def gen_graph_file(self, obj_list, file, mode):
		# mode: 'all', 'caller', 'callee'
		ref_set = set()
		inter_obj = []
		assert(type(obj_list) == list)
		if mode == 'all' or mode == 'caller':
			for caller in obj_list:
				if caller in self.caller_dict:
					for callee in self.caller_dict[caller]:
						if caller != callee:
							ref_set.add((caller, callee))
		if mode == 'all' or mode == 'callee':
			for callee in obj_list:
				if callee in self.callee_dict:
					for caller in self.callee_dict[callee]:
						if caller != callee:
							ref_set.add((caller, callee))
		ref_list = list(ref_set)
		for e in obj_list:
			if e in self.caller_dict or e in self.callee_dict:
				inter_obj.append(e)
		
		dig = Digraph(ref_list)
		dig.set_hight_light(inter_obj)
		dig.gen_graph(file)

	def gen_graph_file_with_group(self, group, file):
		ref_list = []
		for caller in self.caller_dict:
			for callee in self.caller_dict[caller]:
				ref_list.append((caller, callee))
		dig = Digraph(ref_list)
		dig.set_group(group)
		dig.gen_graph(file)

#########################################################
def parse_flat_tree(lines, cond_list):
	''' 解析有层次结构的文件，比如
	=================
	xxx.a
		xxx.o
			fun1
			fun2
		xxx.o
	xxx.a
	=================
	@return [(data, [children]), ...]
	'''
	tree = [('root', [])]
	lvl_list = [0] * (len(cond_list) + 1)
	lvl_list[0] = tree[0]
	last_lvl = 0
	for line in lines:
		line = line.strip()
		if not line :continue
		for i, cond in enumerate(cond_list):
			cur_lvl = i + 1
			data = cond(line)
			if data:
				if cur_lvl <= last_lvl + 1:
					lvl_list[cur_lvl-1][1].append((data,[]))
					lvl_list[cur_lvl] = lvl_list[cur_lvl-1][1][-1]
					last_lvl = cur_lvl
				else:
					print cur_lvl, last_lvl
					print lvl_list
					print line
					raise BaseException
				break
	return tree[0][1]


def read_obj_symb_list(file):
	def cond_1(line):
		if line.endswith('.o:'):
			return line[:-3]
		elif line.endswith('.obj:'):
			return line[:-5]
		elif line.endswith('.o):'):
			return line[line.find('(')+1 : -4]
	def cond_2(line):
		for tag in ('U ', 'T ', 'R ', 'D ', 'B '):
			if tag in line:
				return (tag, line[line.find(tag)+len(tag):])
	
	lines = open(file, 'rb').readlines()
	obj_tree = parse_flat_tree(lines, [cond_1, cond_2])
	
	T_symb_dict = {}  # {symb:objName, ...}
	U_symb_list = []  # [(symb, obj), ...]
	for obj in obj_tree:
		obj_name = obj[0]
		for symb in obj[1]:
			if symb[0][0] in ('T ', 'D ', 'R ', 'B '):
				if symb[0][0] in T_symb_dict:
					raise BaseExcept
				else:
					T_symb_dict[symb[0][1]] = obj_name
			else:
				U_symb_list.append((symb[0][1], obj_name))
	symb_ref_list = []
	for u in U_symb_list:
		if u[0] in T_symb_dict:
			symb_ref_list.append((u[1], T_symb_dict[u[0]], u[0]))
	
	undef_sym_set = set()
	unused_sym_set = set()
	U_symb = sorted(set([e[0] for e in U_symb_list]))
	for u in U_symb_list:
		if u[0] not in T_symb_dict: undef_sym_set.add(u[0])
	for t in T_symb_dict:
		if t not in U_symb: 
			unused_sym_set.add(t)
			
	return (symb_ref_list, list(undef_sym_set), list(unused_sym_set), list(T_symb_dict))


###############################################
################  main  #######################

if len(sys.argv[1:]) != 2:
	print 'obj-symb-ref obj_symb.txt output_dir'
	sys.exit(1)	


obj_sym_file = sys.argv[1]
output_dir = sys.argv[2]

if not os.path.exists(output_dir):
	os.mkdir(output_dir)

symb_ref_list, undef_sym_list, unused_sym_list, export_sym_list = read_obj_symb_list(obj_sym_file)

symb_fd = open(output_dir + os.sep + 'symb-list.txt', 'wb')
symb_fd.write('*'*20 + ' [undef-symb-list] ' + '*'*20 + '\n')
for sym in sorted(undef_sym_list):
	symb_fd.write('\t' + str(sym) + '\n')

symb_fd.write('\n' + '*'*20 + ' [unused-symb-list] ' + '*'*20 + '\n')
for sym in sorted(unused_sym_list):
	symb_fd.write('\t' + str(sym) + '\n')

symb_fd.write('\n' + '*'*20 + ' [export-symb-list] ' + '*'*20 + '\n')
for sym in sorted(export_sym_list):
	symb_fd.write('\t' + str(sym) + '\n')
symb_fd.close()

fd = open(output_dir + os.sep + 'ref.txt', 'wb')
ref = RefGraph(symb_ref_list)
all_obj = ref.get_obj_list()
ref.print_ref_data(all_obj, fd)
for obj in all_obj:
	ref.gen_graph_file([obj], output_dir + os.sep + obj, 'all')
if len(all_obj) < 500:
	ref.gen_graph_file(all_obj, output_dir + os.sep + 'all', 'all')

