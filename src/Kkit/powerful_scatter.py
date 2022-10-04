from . import utils
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.decomposition import PCA
from prince import CA
from adjustText import adjust_text

def PCA_2D(vecs):
    if isinstance(vecs, str):
        vecs = utils.load_result(vecs)
    pca = PCA(n_components=2,svd_solver='full')
    PCA_res = pca.fit_transform(vecs)
    return PCA_res

def CA_2D(vecs):
    if isinstance(vecs, str):
        vecs = utils.load_result(vecs)
    ca = CA(n_components=2, n_iter=100, copy=True, check_input=True, engine='sklearn')
    CA_res = ca.fit_transform(vecs).row_coordinates(vecs)
    return CA_res

def plot_2D(vecs, s=8, labels=None, scatter_color="red", label_color="black", label_font_size=16, xy_ticks_font_size=14, splines_lw=4, arrow_lw=1, xy_lim=None, xy_majoy_locator=None, xy_equal=True): 
    ax = plt.gca()
    
    if xy_equal:
        plt.axis("equal")
    if xy_lim != None:
        plt.xlim(xy_lim[0])
        plt.ylim(xy_lim[1])
    if xy_majoy_locator != None:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(xy_majoy_locator[0]))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(xy_majoy_locator[1]))
    plt.axvline(0, color="gray")
    plt.axhline(0, color="gray")

    plt.scatter(vecs[:,0], vecs[:,1], s=s, color=scatter_color)

    if labels != None:
        new_texts = [plt.text(x_, y_, text, fontsize=label_font_size, color=label_color) for x_, y_, text in zip(vecs[:,0], vecs[:,1], labels)]
        num = adjust_text(new_texts, 
            only_move={'text': 'xy', "objects": "xy", "points": "xy"},
            arrowprops=dict(arrowstyle='-', linestyle="-.", color='silver',lw=arrow_lw),
            precision=0.0001)

    ax.spines['bottom'].set_linewidth(splines_lw)
    ax.spines['left'].set_linewidth(splines_lw)
    ax.spines['right'].set_linewidth(splines_lw)
    ax.spines['top'].set_linewidth(splines_lw)

    plt.xticks(fontsize=xy_ticks_font_size)
    plt.yticks(fontsize=xy_ticks_font_size)

    # plt.xlim = XY_range
    # plt.ylim = XY_range

def adjusted_label(vecs, labels, font_color="black", arrow_linestyle="-.", arrow_color="silver", font_size=16, arrow_lw=1):
    X = vecs[:,0]
    y = vecs[:,1]
    new_texts = [plt.text(x_, y_, text, fontsize=font_size, color=font_color) for x_, y_, text in zip(X, y, labels)]
    num = adjust_text(new_texts, 
        only_move={'text': 'xy', "objects": "xy", "points": "xy"},
        arrowprops=dict(arrowstyle='-', linestyle=arrow_linestyle, color=arrow_color,lw=arrow_lw),
        precision=0.0001)
    return num