from urllib.parse import urlencode
from typing import Optional, Dict, List, Union
from django.http import QueryDict


class Bootstrap5Pagination:
    """
    Django + Bootstrap 5 通用分页组件
    - 支持省略号（...）
    - 支持 Bootstrap5 尺寸 / 对齐
    - 支持 QueryDict
    - 符合 Bootstrap 5 官方语义 & 无障碍规范
    """
    # Bootstrap 5 样式常量
    DEFAULT_CLASSES = {
        'nav': 'pagination',
        'nav_sm': 'pagination-sm',
        'nav_lg': 'pagination-lg',
        'item': 'page-item',
        'link': 'page-link',
        'active': 'active',
        'disabled': 'disabled',
        'justify_start': 'justify-content-start',
        'justify_center': 'justify-content-center',
        'justify_end': 'justify-content-end'
    }

    def __init__(
            self,
            current_page: Union[str, int],
            all_count: int,
            base_url: str,
            query_params: Union[Dict, QueryDict],
            per_page: int = 10,
            pager_page_count: int = 11,
            show_info: bool = True,
            size: Optional[str] = 'sm',  # sm, lg, None
            justify: str = 'start',  # start, center, end
            aria_label: str = "分页导航",
            page_param: str = "page",
    ):
        """
        Bootstrap5样式 分页组件
        :param current_page: 当前页码
        :param all_count: 总记录数量
        :param base_url: 基础url
        :param query_params: 查询参数字典
        :param per_page: 每页记录数量
        :param pager_page_count: 显示的页码数量
        :param show_info: 是否显示统计信息
        :param size: 分页尺寸 （sm/lg/none）
        :param justify: 对齐方式 (start/center/end)
        :param aria_label: ARIAL标签，无障碍支持
        """
        # 基础设置
        self.base_url = base_url
        self.per_page = max(1, per_page)
        self.all_count = max(0, all_count)
        self.pager_page_count = max(5, pager_page_count)
        self.show_info = show_info
        self.aria_label = aria_label
        self.page_param = page_param

        # Bootstrap5样式
        self.size = size
        self.justify = justify

        # 处理查询参数
        self.query_params = self._prepare_query_params(query_params)

        # 计算分页核心数据，先计算分页总数，再验证当前页码
        self.pager_count = self._calculate_total_pages()
        self.current_page = self._validate_current_page(current_page)

        # 计算其他分页
        self.half_pager_page_count = self.pager_page_count // 2
        self.start, self.end = self._calculate_record_range()

        # 生成HTML
        self.html = self.generate_html()

    # ======================基础计算======================

    def _validate_current_page(self, current_page: Union[str, int]) -> int:
        """验证并且返回合法的当前页码"""
        try:
            page = int(current_page) if current_page else 1
            return max(1, min(page, self.pager_count)) if self.pager_count > 0 else 1
        except (ValueError, TypeError):
            return 1

    def _calculate_total_pages(self) -> int:
        """计算总页数"""
        if self.all_count == 0:
            return 0
        return (self.all_count + self.per_page - 1) // self.per_page

    def _calculate_record_range(self) -> tuple:
        """计算当前页码的记录范围"""
        if self.pager_count == 0:
            return 0, 0
        start = (self.current_page - 1) * self.per_page
        end = min(start + self.per_page, self.all_count)
        return start, end

    # ---------- Query 参数 ----------
    def _prepare_query_params(self, query_params: Union[Dict, QueryDict]) -> Dict:
        """
        预处理查询参数（兼容 Django QueryDict 和普通字典）
        :param query_params: 查询参数（Django QueryDict 或普通字典）
        :return: 可变的参数字典
        """
        # 处理 Django QueryDict 特殊情况
        if isinstance(query_params, QueryDict):
            # 先复制（Django QueryDict.copy() 可能返回不可变对象）
            params = query_params.dict()
        else:
            # 普通字典直接复制
            params = query_params.copy()

        # 移除可能存在的page参数
        params.pop(self.page_param, None)
        return params

    def get_page_url(self, page: int) -> str:
        params = self.query_params.copy()
        params[self.page_param] = page
        return f'{self.base_url}?{urlencode(params)}'

    # ================Bootstrap5 样式==============

    def _get_nav_classes(self) -> str:
        """获取导航容器的CSS类"""
        classes = [self.DEFAULT_CLASSES['nav']]

        # 添加尺寸类
        if self.size == 'sm':
            classes.append(self.DEFAULT_CLASSES['nav_sm'])
        elif self.size == 'lg':
            classes.append(self.DEFAULT_CLASSES['nav_lg'])

        # 添加对齐类
        justify_class = self.DEFAULT_CLASSES[f'justify_{self.justify}']
        classes.append(justify_class)

        return ' '.join(classes)

    def build_li(
            self,
            page: int,
            text: Optional[str] = None,
            active: bool = False,
            disabled: bool = False,
    ) -> str:
        """
        构建 Bootstrap 5 标准的分页项

        :param page: 页码
        :param text: 显示文本
        :param active: 是否激活
        :param disabled: 是否禁用
        :return: 格式化的li标签
        """
        text = text or str(page)
        li_classes = [self.DEFAULT_CLASSES['item']]

        # 添加状态类
        if active:
            li_classes.append(self.DEFAULT_CLASSES['active'])
        if disabled:
            li_classes.append(self.DEFAULT_CLASSES['disabled'])

        if disabled:
            return (
                f'<li class="{" ".join(li_classes)}">'
                f'<span class="{self.DEFAULT_CLASSES["link"]}">{text}</span>'
                f'</li>'
            )

        aria = ' aria-current="page"' if active else ''
        return (
            f'<li class="{" ".join(li_classes)}">'
            f'<a class="{self.DEFAULT_CLASSES["link"]}" '
            f'href="{self.get_page_url(page)}"{aria}>{text}</a>'
            f'</li>'
        )

    def get_display_page_range(self) -> List[int]:
        """计算需要显示的页码范围（包含省略号逻辑）"""
        if self.pager_count <= 0:
            return []

        # 如果总页数小于等于显示数量，直接返回所有页码
        if self.pager_count <= self.pager_page_count:
            return list(range(1, self.pager_count + 1))

        # 核心页码集合（确保显示第一页、最后一页和当前页附近的页码）
        pages = {1, self.pager_count}

        # 计算当前页附近的页码范围
        start = max(self.current_page - self.half_pager_page_count, 2)
        end = min(self.current_page + self.half_pager_page_count, self.pager_count - 1)

        # 添加当前页附近的页码
        pages.update(range(start, end + 1))

        return sorted(pages)

    def _build_info_item(self) -> str:
        """构建统计信息项（Bootstrap 5 样式）"""
        if not self.show_info or self.all_count == 0:
            return ''

        # 统计信息文本
        info_text = (
            f'共 {self.all_count} 条记录 ·'
            f'第 {self.current_page} 页 / 共 {self.pager_count} 页 · '
            f'每页 {self.per_page} 条'
        )

        # Bootstrap 5 样式的信息项
        return (
            f'<li class="{self.DEFAULT_CLASSES["item"]} {self.DEFAULT_CLASSES["disabled"]}">'
            f'<span class="{self.DEFAULT_CLASSES["link"]}">{info_text}</span>'
            f'</li>'
        )

    def generate_html(self) -> str:
        """生成完整的 Bootstrap 5 分页HTML"""
        # 如果没有记录，返回空
        if self.all_count == 0:
            return '<div class="text-muted">暂无数据</div>'

        # 初始化HTML列表
        html = [
            f'<nav aria-label="{self.aria_label}">',
            f'<ul class="{self._get_nav_classes()}">'
        ]

        # 上一页按钮
        html.append(
            self.build_li(
                self.current_page - 1,
                '« 上一页',
                disabled=self.current_page == 1
            )
        )

        # 生成页码
        page_range = self.get_display_page_range()
        last_page = 0

        for page in page_range:
            # 添加省略号
            if last_page and last_page + 1 < page:
                html.append(
                    f'<li class="{self.DEFAULT_CLASSES["item"]} {self.DEFAULT_CLASSES["disabled"]}">'
                    f'<span class="{self.DEFAULT_CLASSES["link"]}">…</span>'
                    f'</li>'
                )

            # 添加页码项
            html.append(
                self.build_li(
                page,
                active=(page == self.current_page),
                )
            )

            last_page = page

        # 下一页按钮
        html.append(
            self.build_li(
                self.pager_count + 1,
                '下一页 »',
                disabled=self.current_page == self.pager_count
            )
        )

        # 添加统计信息
        info_html = self._build_info_item()
        if info_html:
            html.append(info_html)

        # 闭合标签
        html.extend(['</ul>', '</nav>'])

        return ''.join(html)

    # ===============Django友好端口===================

    @property
    def page_slice(self):
        """
        queryset切片
        :return:
        """
        return slice(self.start, self.end)

    def __str__(self) -> str:
        """返回HTML字符串"""
        return self.html

    def __repr__(self) -> str:
        """返回调试信息"""
        return (
            f"<Bootstrap5Pagination "
            f"current_page={self.current_page} "
            f"total_pages={self.pager_count} "
            f"total_records={self.all_count}>"
        )
