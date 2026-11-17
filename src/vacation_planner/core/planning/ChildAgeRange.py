"""Narrow published selector-label grammar, never a guess from hotel prose."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ChildAgeRange:
    minimum: int
    maximum: int
    label: str

    @classmethod
    def parse(cls,label):
        text=' '.join(label.casefold().replace('–','-').replace('—','-').split()).strip(' :*')
        patterns=[(r'(?:kinder|kind|children|child)\s*\(?\s*(?:unter|under)\s+(\d{1,2})(?:\s*(?:jahre|years|years old))?\s*\)?',False),
                  (r'(?:kinder|kind|children|child)\s*\(?\s*(?:bis(?: einschließlich)?|up to)\s+(\d{1,2})(?:\s*(?:jahre|years|years old))?\s*\)?',True)]
        for pattern,inclusive in patterns:
            match=re.fullmatch(pattern,text)
            if match:
                maximum=int(match[1])-(not inclusive)
                if 0<=maximum<=17:return cls(0,maximum,label)
        match=re.fullmatch(r'(?:kinder|kind|children|child)\s*\(?\s*(?:(?:age|ages|aged)\s+)?(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*(?:jahre|years|years old)?\s*\)?',text)
        if match and 0<=int(match[1])<=int(match[2])<=17:return cls(int(match[1]),int(match[2]),label)
        return None

    def accepts(self,ages):return all(type(a) is int and self.minimum<=a<=self.maximum for a in ages)

    def to_dict(self):return dict(minimum=self.minimum,maximum=self.maximum,label=self.label,contract='selector-age-range-v1')
