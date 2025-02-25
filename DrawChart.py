# 开发目的
# 1.目录循环获取数据
# 2.生成新Excel画图
import os
import sys
import pandas as pd
import xlsxwriter
import random


class DrawChart:
    def __init__(self, path):
        self.path = path
        self.workbook = xlsxwriter.Workbook(os.path.expanduser('~/Desktop/output.xlsx'))
        self.worksheet = self.workbook.add_worksheet('sheet_test')
        self.index = 0
        self.col = 1
        self.names = []
        self.data_list = {}

    # 目录循环获取Path
    def get_excel_path(self):
        for root, dirs, files in os.walk(self.path):
            if 'FG_summary.csv' in files:
                df_csv = pd.read_csv(os.path.join(root, 'FG_summary.csv'), header=None)
                speed = df_csv.iloc[0, -1]
                new_files = sorted(files)
                file_path = os.path.join(root, new_files[0])
                airflow = file_path.split('/')[-2]
                self.names.append(f'{airflow}-{speed}')
                self.get_excel_data(file_path)
            # for name in files:
            #     file_path = os.path.join(root, name)
            #     if '.xlsx' in name:
            #         self.names.append(file_path.split('/')[-2])
            #         # self.get_excel_data(file_path)
            #         break
        self.write_index(range(1, self.index+1))
        self.draw_chart()

    # 读取文件中的data数据
    def get_excel_data(self, path):
        df = pd.read_excel(path)
        self.index = self.index if self.index > len(df['index']) else len(df['index'])
        self.data_list[self.names[-1]] = df['data']
        # self.write_data(df['data'])
        # self.col += 1

    def write_col(self, num, data):
        row_index = 1
        for item in data:
            self.worksheet.write(row_index, num, item)
            row_index += 1

    def write_data(self, name, data):
        # 循环写title
        # self.worksheet.write(0, self.col, self.names[-1])
        # 循环写data
        # self.write_col(self.col, data)
        # 写title(第一行)
        self.worksheet.write(0, self.col, name)
        # 写数据
        self.write_col(self.col, data)

    def write_index(self, data):
        self.worksheet.write(0, 0, 'index')
        self.write_col(0, data)
        # 对date_list中的数据进行排序，循环写入
        self.new_names = sorted(self.data_list.keys(), key=lambda x: x.split('-')[0])
        for new_key in self.new_names:
            self.write_data(new_key, self.data_list[new_key])
            self.col += 1




    # 定义一个函数来生成随机颜色
    def random_color(self):
        return f'#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}'


    def get_add_series(self, name, location):
        color = self.random_color()
        return {
            'line': {'color': color},
            'name': name,
            'categories': "=sheet_test!$A$2:$A$%s" % self.index,
            'values': "=sheet_test!$%s$2:$%s$%s" % (location, location, self.index),
        }

    def generate_letter_combinations(self, length):
        result = []
        # 从0开始，因为A的ASCII值是65，我们使用65-64来对齐
        for num in range(length):
            # 确定当前的字母组合需要几个字母
            quotient = num
            combination = ""
            while quotient >= 26:
                # 每次除以26，取余数，然后将商作为下一次循环的数字
                remainder = quotient % 26
                quotient = quotient // 26
                combination = chr(remainder + 65) + combination
            # 最后加上剩余的字母
            combination = chr(quotient + 65) + combination
            # 如果组合的长度大于1，我们需要减去一个26，因为'AA'实际上是26，不是52
            if len(combination) > 1:
                combination = chr(ord(combination[0]) - 1) + combination[1:]
            result.append(combination)
        return result[1:]

    def draw_chart(self):
        chart = self.workbook.add_chart({'type': 'line'})
        shape_name = u"Relationship diagram between airflow, speed, and force Working pressure value:0.248MPa"
        chart.set_title({'name': shape_name})
        chart.set_x_axis({'name': u'index'})
        chart.set_y_axis({'name': u'data'})



        # 获取列对应的字母
        col_list = self.generate_letter_combinations(self.col + 2)
        col_name = col_list[-1]
        chart_list = col_list[:-2]

        # 循环绘图
        row = 0
        for i in chart_list:
            chart.add_series(self.get_add_series(self.new_names[row], i))
            row += 1

        self.worksheet.insert_chart(f'{col_name}5', chart)
        self.workbook.close()


if __name__ == "__main__":
    dc = DrawChart(sys.argv[1])
    dc.get_excel_path()
