import untypy

untypy.enable()


def show_price_for_screw(amount: int) -> None:
    base_price = 10  # cents per screw
    print(f"Screws: {amount * base_price} cents")


show_price_for_screw("3")
