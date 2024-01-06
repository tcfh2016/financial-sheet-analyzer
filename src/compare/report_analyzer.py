import os
import pandas as pd
import matplotlib.pyplot as plt
import report.balance as balance
import report.income as income
import report.cashflow as cashflow


class ReportAnalyzer():
    def __init__(self, args, data_path, config_path):
        self.data_path = data_path
        self.args = args
        self.config_path = config_path

        self.stock_dict = {}
        self.balance_df = []
        self.income_df = []
        self.cashflow_df = []
        self.balance_analyzer = []
        self.income_analyzer = []
        self.cashflow_analyzer = []

    def joint_analyze_profit(self):
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.sans-serif'] = ['SimHei']
        fig, axes = plt.subplots(nrows=2, ncols=1)

        # joint analysis for income items and balance items
        ib_df = pd.DataFrame(self.income_df[0].loc['利润总额(万元)'])
        ib_df['负债合计(万元)'] = self.balance_df[0].loc['负债合计(万元)']
        ib_df['净资产(万元)'] = self.balance_df[0].loc['所有者权益(或股东权益)合计(万元)']
        print(ib_df)
        ib_df_plot = ib_df.plot(ax=axes[0], figsize=(8, 6))
        ib_df_plot.set_ylabel("数值")

        # analysis rate of return
        df = pd.DataFrame(self.income_df[0].loc['利润总额(万元)'])
        df['净利润(万元)'] = self.income_df[0].loc['净利润(万元)']
        df['资产总计(万元)'] = self.balance_df[0].loc['资产总计(万元)']
        df['净资产(万元)'] = self.balance_df[0].loc['所有者权益(或股东权益)合计(万元)']
        df['总资产报酬率'] = df['利润总额(万元)'] / df['资产总计(万元)']
        df['净资产报酬率'] = df['净利润(万元)'] / df['净资产(万元)']

        rr_df = pd.DataFrame(df, columns=['总资产报酬率', '净资产报酬率'])
        print(rr_df)
        rr_df_plot = rr_df.plot(ax=axes[1], figsize=(8, 6))
        rr_df_plot.set_ylabel('百分比')
        rr_df_plot.set_xlabel('日期')
        vals = rr_df_plot.get_yticks()
        rr_df_plot.set_yticklabels(['{:,.2%}'.format(x) for x in vals])

        plt.show()

    def estimate_asset(self):
        # print(self.asset_df.loc['流动资产合计(万元)'])
        df_asset_es = pd.DataFrame(self.balance_df[0].loc['资产总计(万元)'])
        df_asset_es['存货(万元)'] = self.balance_df[0].loc['存货(万元)']
        df_asset_es['流动资产合计(万元)'] = self.balance_df[0].loc['流动资产合计(万元)']
        df_asset_es['负债合计(万元)'] = self.balance_df[0].loc['负债合计(万元)']
        df_asset_es['流动负债合计(万元)'] = self.balance_df[0].loc['流动负债合计(万元)']
        df_asset_es['实收资本(或股本)(万元)'] = self.balance_df[0].loc['实收资本(或股本)(万元)']

        # 营运资金
        df_asset_es['营运资金'] = df_asset_es['流动资产合计(万元)'] - df_asset_es['流动负债合计(万元)']
        # 酸性测试
        df_asset_es['酸性测试'] = ['True' if x>0 else 'False' for x in df_asset_es['营运资金'] - df_asset_es['存货(万元)']]
        # 每股清算价值 ~ 流动资产价值
        df_asset_es['流动资产价值'] = df_asset_es['营运资金'] / df_asset_es['实收资本(或股本)(万元)']
        # 每股账面价值
        df_asset_es['账面价值'] = (df_asset_es['资产总计(万元)'] - df_asset_es['负债合计(万元)']) / df_asset_es['实收资本(或股本)(万元)']
        # 资产负债率
        df_asset_es['资产负债率'] = (df_asset_es['负债合计(万元)'] / df_asset_es['资产总计(万元)'])
        df_asset_es.T.to_csv("asset_estimate.csv", sep=',', encoding='utf-8-sig')
        #print(df_asset_es.T)

    def joint_analyze_cashflow(self):
        plt.rcParams['font.sans-serif'] = ['SimHei']
        fig, axes = plt.subplots(nrows=2, ncols=1)

        # joint analysis for income items and cashflow items
        ic_df = pd.DataFrame(self.cashflow_df[0].loc['销售商品、提供劳务收到的现金(万元)'])
        ic_df['营业收入(万元)'] = self.income_df[0].loc['营业收入(万元)']
        ic_df_plot = ic_df.plot(ax=axes[0], figsize=(8, 6))
        ic_df_plot.set_ylabel("数值")
        print(ic_df)

        # joint analysis for balance items and cashflow items
        bc_df = pd.DataFrame(self.cashflow_df[0].loc['期末现金及现金等价物余额(万元)'])
        bc_df['短期借款(万元)'] = self.balance_df[0].loc['短期借款(万元)']
        bc_df['长期借款(万元)'] = self.balance_df[0].loc['长期借款(万元)']
        print(bc_df)
        liability_dp = bc_df.plot(ax=axes[1], figsize=(8, 6))
        liability_dp.set_xlabel("日期")
        liability_dp.set_ylabel("数值")
        plt.show()

    def prepare_dataset(self):
        # 构建股票编码和名称字典
        stock_list_file = os.path.join(self.config_path, "stock_list.txt")
        if os.access(stock_list_file, os.R_OK):
            with open(stock_list_file, "r", encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    l = line.split(',')
                    self.stock_dict[l[0]] = l[1]
                # print(self.stock_dict)
        else:
            print("Can't find stock list file.")

        # 读取每只股票的财务报表信息
        for stock in self.args.stock:
            balance_filename = "zcfzb" + stock + ".csv"
            income_filename = "lrb" + stock + ".csv"
            cashflow_filename = "xjllb" + stock + ".csv"
            balance_datafile = os.path.join(self.data_path, balance_filename)
            income_datafile = os.path.join(self.data_path, income_filename)
            cashflow_datafile = os.path.join(self.data_path, cashflow_filename)
            if os.access(balance_datafile, os.R_OK) and \
               os.access(income_datafile, os.R_OK) and \
               os.access(cashflow_datafile, os.R_OK):
                self.balance_analyzer.append(balance.BalanceSheetAnalyzer(balance_datafile))
                self.income_analyzer.append(income.IncomeStatementAnalyzer(income_datafile))
                self.cashflow_analyzer.append(cashflow.CashflowStatementAnalyzer(cashflow_datafile))
            else:
                print("Can't find {} and {}".format(self.balance_datafile, self.income_datafile))
                os._exit(0)

    def compare_multi_stocks(self, stocks_df, title):
        self.multi_stocks_df = pd.DataFrame(stocks_df[0].index)
        self.multi_stocks_df = self.multi_stocks_df.set_index(['报告日期'])

        # 保存多只股票最近一年的资产负债表/利润表数据
        filter_condition = [True] * len(stocks_df[0]['2018-12-31'])
        for i in range(len(self.args.stock)):
            stock_no = self.args.stock[i]
            stock_name = self.stock_dict[stock_no]
            self.multi_stocks_df[stock_name] = stocks_df[i]['2018-12-31']
            filter_condition &= self.multi_stocks_df[stock_name] > 10000
            # print(filter_condition)
        # print(self.multi_stocks_asset_df)

        # 修正x轴标签过长，删除其中包含的'(万元)'字段
        df_for_plot = self.multi_stocks_df[filter_condition]
        index = pd.Series(df_for_plot.index)
        index.replace(to_replace='\(万元\)', value='', regex=True, inplace=True)
        df_for_plot.index = index

        # print(df_for_plot)
        if title == '资产负债表':
            df_for_plot_percentage = df_for_plot[:] / df_for_plot.loc['资产总计']
        elif title == '利润表':
            df_for_plot_percentage = df_for_plot[:] / df_for_plot.loc['营业总收入']
        else:
            pass

        # print(df_for_plot_percentage)

        plt.rcParams['font.sans-serif'] = ['SimHei']
        fig, axes = plt.subplots(nrows=2, ncols=1)
        dp = df_for_plot.plot(ax=axes[0], figsize=(8,6), kind='bar')
#        dp.set_xlabel("项目")
        dp.set_ylabel("价值（万元）")
        dp.set_xticks(range(len(df_for_plot.index)))
        dp.set_xticklabels([], rotation=90)

        dpp = df_for_plot_percentage.plot(ax=axes[1], figsize=(8,6))
        dpp.set_xlabel("项目")
        dpp.set_ylabel("百分比")
        dpp.set_xticks(range(len(df_for_plot.index)))
        dpp.set_xticklabels(df_for_plot.index, rotation=90)

        plt.subplots_adjust(wspace=0.6, hspace=0, left=0.1, bottom=0.22, right=0.96, top=0.96)
        plt.show()

    def analyze_single_stock(self):
        if (self.args.option == 'balance'):
            self.balance_analyzer[0].analyze()
            #self.estimate_asset()
        elif (self.args.option == 'income'):
            self.income_analyzer[0].analyze()
            self.joint_analyze_profit()
        elif (self.args.option == 'cashflow'):
            self.cashflow_analyzer[0].analyze()
            self.joint_analyze_cashflow()
        else:
            print("Invalid option !")

    def analyze_multipy_stocks(self):
        if (self.args.option == 'balance'):
            self.compare_multi_stocks(self.balance_df, '资产负债表')
        elif (self.args.option == 'income'):
            self.compare_multi_stocks(self.income_df, '利润表')
        else:
            print("Invalid option !")

    def analyze(self):
        for i in range(len(self.args.stock)):
            self.balance_df.append(self.balance_analyzer[i].numberic_df)
            self.income_df.append(self.income_analyzer[i].numberic_df)
            self.cashflow_df.append(self.cashflow_analyzer[i].numberic_df)
        if ((len(self.args.stock) == 1)):
            self.analyze_single_stock()
        else:
            self.analyze_multipy_stocks()

    def start(self):
        self.prepare_dataset()
        self.analyze()
