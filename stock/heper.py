from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from club.models import Club
    from core.models import User
    from stock.models import Stock


def can_be_edited_by(user: User, club: Club):
    return user.groups.contains(club.stock_group) or user.is_root


def can_be_view_by(user: User, club: Club, stock: Stock):
    return can_be_edited_by(user, club) or (
        stock.can_be_view_by_board and user.is_in_group(pk=club.stock_group)
    )
