from enum import Enum


class Number(Enum):
    """詰将棋の手数
    """
    SEVEN = (7, 'seven')
    NINE = (9, 'nine')
    ELEVEN = (11, 'eleven')
    THIRTEEN = (13, 'thirteen')
    FIFTEEN = (15, 'fifteen')
    NINETEEN = (19, 'nineteen')

    def __init__(self, int_number, str_number):
        self.__int_number = int_number
        self.__str_number = str_number

    @property
    def int_number(self):
        return self.__int_number

    @property
    def str_number(self):
        return self.__str_number

    def __str__(self):
        return str(self.__int_number)

    @classmethod
    def value_of(cls, target):
        """引数に対応するNUMBER返却する。
        Parameters
        --------------------------
        number : str or int
            数字
        Returns
        --------------------------
        Number
            数字に対応するNumber　ない場合はエラー
        """
        if isinstance(target, str):
            for e in Number:
                if e.str_number == target:
                    return e
        elif isinstance(target, int):
            for e in Number:
                if e.int_number == target:
                    return e
        raise ValueError()
