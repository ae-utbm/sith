import { counterAddSellersToCounter, counterRemoveSellersFromCounter } from "#openapi";

export async function addSellers(counterId: number, sellers: number[]) {
    const res = await counterAddSellersToCounter({
        body: { users_id: sellers },
        path: { counter_id: counterId },
    });
    return res.response;
}

export async function removeSellers(counterId: number, sellers: number[]) {
    const res = await counterRemoveSellersFromCounter({
        body: { users_id: sellers },
        path: { counter_id: counterId },
    });
    return res.response;
}

// Alpine.js component pour la suppression d'un utilisateur d'un comptoir
(window as any).removeUserFromCounter = (counterId: number, userId: number) => ({
    loading: false,
    removed: false,
    message: "",
    success: false,
    async remove() {
        this.loading = true;
        this.message = "";
        this.success = false;
        try {
            await removeSellers(counterId, [userId]);
            this.message = gettext("User removed successfully.");
            this.success = true;
            this.removed = true;
        } catch (e) {
            this.message = gettext("Error removing user.");
            this.success = false;
        }
        this.loading = false;
    }
});
