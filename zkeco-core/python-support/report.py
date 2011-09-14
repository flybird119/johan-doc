#coding=utf-8
from traceback import print_exc
from reportlab.platypus import *
from reportlab.lib.styles import PropertySet, getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.codecharts import KutenRowCodeChart, hBoxText
from reportlab.pdfbase import pdfmetrics, cidfonts
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch
import reportlab


""" A类就是我们通常说的大度纸，整张纸的尺寸是889*1194mm，可裁切A1(大对开，570*840mm）、A2（大四开，420*570mm）、A3（大八开，285*420mm）、A4（大十六开，210*285mm）、A5（大三十二开，142.5*210mm）……；
  B类就是我们通常说的正度纸，整张纸的尺寸是787*1092mm，可裁切B1(正对开，520*740mm）、B2（正四开，370*520mm）、B3（正八开，260*370mm）、B4（正十六开，185*260mm）、B5（正三十二开，130*185mm）"""
page_sizes={"A0":(889, 1194), "A1":(570, 840), "A2":(420, 570),
            "A3":(285, 420), "A4":(210, 285), "A5":(142.5, 210),
            "B0":(787, 1092), "B1":(520, 740), "B2":(370, 520),
            "B3":(260, 370), "B4":(185, 260), "B5":(130, 185),
    }

class Report(object):
    def __init__(self):
        self.width, self.height=page_sizes["A4"]
        reportlab.lib.fonts.ps2tt = lambda psfn: ('STSong-Light', 0, 0)
        reportlab.lib.fonts.tt2ps = lambda fn,b,i: 'STSong-Light'
        reportlab.lib.styles.ParagraphStyle.defaults['wordWrap'] = "CJK"
        self.page_tail=None
        self.grid_head_height=30
        self.row_height=15
        self.style_grid = TableStyle(
            [('GRID', (0,0), (-1,-1), 0.25, colors.gray),
             ('BOX',  (0,0), (-1, -1), 0.5, colors.black),
             ('ALIGN', (0,0), (-1, -1), 'LEFT'),
             ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME',(0,0),(-1,-1),'STSong-Light'),
            ('FONTSIZE',(0,0),(-1,-1), 8),
            ('LEFTPADDING',(0,0),(-1,-1), 1),
            ('RIGHTPADDING',(0,0),(-1,-1), -5),
            ]
            )
        self.style_table = TableStyle(
            [
             ('ALIGN', (0,0), (-1, -1), 'LEFT'),
             ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME',(0,0),(-1,-1),'STSong-Light'),
            ('FONTSIZE',(0,0),(-1,-1), 8),
            ('LEFTPADDING',(0,0),(-1,-1), 5),
            ('RIGHTPADDING',(0,0),(-1,-1), 20),
            ]
            )
        self.styleSheet = getSampleStyleSheet()
        self.styNormal = self.styleSheet['Normal']
        self.styNormal.spaceBefore = 6
        self.styNormal.spaceAfter = 6
        font = cidfonts.UnicodeCIDFont('STSong-Light')
        pdfmetrics.registerFont(font)
       
        self.style_head_text=ParagraphStyle(
                name="base",
                fontName="STSong-Light",
                leading=10,
                leftIndent=0,
                firstLineIndent=-10,
                spaceBefore = -10,
                spaceAfter = 1,
                fontSize=8,
                wordWrap='CJK',
                )
        self.style_grid_head=ParagraphStyle(
                name="base",
                fontName="STSong-Light",
                leading=10,
                leftIndent=0,
                firstLineIndent=0,
                spaceBefore = 1,
                fontSize=8,
                align="CENTER",
                wordWrap='CJK',
                )
        self.style_title = ParagraphStyle(name='normal',
                fontName='STSong-Light',
                fontSize=13,
                leading=30,#1.2*12,
                spaceBefore=1,
                spaceAfter=1,
                parent=self.styleSheet['Heading1'],
                alignment=TA_CENTER,
                wordWrap='CJK',
                )


    def myFirstPage(self, canvas, doc):#页眉，页脚的设置（第一页）
        canvas.saveState()
        canvas.setFont('STSong-Light',10)
        canvas.drawString(self.width*4*inch/210.0, 0.75 * inch, u"第 %d 页" % doc.page)
        canvas.restoreState()
    
    def myLaterPages(self, canvas, doc):#页眉，页脚的设置（除第一页）
        self.myFirstPage(canvas, doc)
   
    def create_a_page_(self, lst, page_rows, rowheights):    
        #页面标头
        if self.page_head: 
            for hp in self.page_head: lst.append(hp)  #添加页面标头

        #表格数据
        cols_count=len(self.colwidths)
        page_rows_count = len(page_rows)
        #表头
        if self.grid_head:
            page_rows_count += 1
        p_rows = self.grid_head and (self.grid_head,) or ()
        for row in page_rows:
            try:
                aaa=tuple(row)+("",)*cols_count
            except TypeError:
                aaa=(row,)+("",)*cols_count
            p_rows+=(aaa[:cols_count],) # for row in page_rows]) #补全每一行的列数并转换为tuple
        if self.fill_grid and (page_rows_count<self.record_per_page):   
            #print "#用空白补全一页的记录，使之达到规定的每页记录数"
            p_rows+=("",)*(self.record_per_page-page_rows_count)
            page_rows_count=self.record_per_page
        lst.append(Table(p_rows, self.colwidths, rowheights[:page_rows_count], self.style))
        #页尾
        if self.page_tail: 
            for hp in self.page_tail: lst.append(hp)
        lst.append(PageBreak())
    def create_a_page(self, lst, page_rows, rowheights):    
        try:
            self.create_a_page_(lst, page_rows, rowheights)
        except:
            print_exc()
    def create_simple_pages(self, rows, page_break_test=None):  #生成全部页面的数据内容
        lst=[]
        total_records_count=len(rows)
        if self.grid_head:
            rowheights = (self.grid_head_height,)
        else:
            rowheights = ()
        #print "record_per_page:",self.record_per_page
        rowheights += (self.row_height,)*self.record_per_page
        if page_break_test: #定义有分页函数
            prev_row=None       #记住上面一行
            page_rows=[]
            for row in rows:
                page_break = page_break_test(prev_row, row) 
                if page_break: #从此行起要另起新页, 把已有的行输出
                     self.create_a_page(lst, page_rows, rowheights)
                     page_rows=[]
                page_rows.append(row)
                prev_row=row
            if page_rows: #最后如果还有没有输出的行的话，直接输出行
                self.create_a_page(lst, tuple(page_rows), rowheights)
        elif self.record_per_page: #按数据行数分页
            for p in range((total_records_count+self.record_per_page-1)/self.record_per_page):
                start_record_index = p*self.record_per_page
                page_rows = rows[start_record_index:start_record_index+self.record_per_page] #取得该页的所有行
                self.create_a_page(lst, tuple(page_rows), rowheights)
        else: #自动分页
                self.create_a_page(lst, tuple(rows), self.grid_head and (self.grid_head_height,) or () + (self.row_height,)*total_records_count)
        return lst
    
    def print_report(self, rows, record_per_page, grid_head=None, page_head=None, page_tail=None, page_break_test=None, fill_grid=True, file_name="temp.pdf"):
        self.style=self.style_grid
        self.record_per_page=record_per_page
        self.page_head=page_head
        self.grid_head=grid_head
        self.page_tail=page_tail
        self.fill_grid=fill_grid
        self.lst=self.create_simple_pages(rows, page_break_test)
        #print self.width, self.height
        SimpleDocTemplate(file_name, pagesize=(self.width*2.9, self.height*2.9)).build(self.lst, 
            onFirstPage=self.myFirstPage,
            onLaterPages=self.myLaterPages)
    def set_page_size(self, paper_name, landscape=False):
        if not landscape:
            self.width, self.height=page_sizes[paper_name]
        else:
            self.height, self.width=page_sizes[paper_name]
 
