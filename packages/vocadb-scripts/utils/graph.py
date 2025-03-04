import matplotlib.pyplot as plt


def graph_values(data: list[tuple[str,int]], xlabel="", ylabel="", title=""):

    x, y = zip(*data)
    plt.bar(x, y)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)

    plt.show()
