from . import utils
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.decomposition import PCA
from prince import CA
import numpy as np
from adjustText import adjust_text

def PCA_2D_plot(vecs_file_path, figsize, s=8, labels=None, label_font_size=16, xy_title_font_size=28, xy_ticks_font_size=14, splines_lw=4, arrow_lw=1, xy_title=None, xy_lim=None, xy_majoy_locator=None, xy_equal=True, save_path=None, dpi=600):
    vecs = utils.load_result(vecs_file_path)
    vecs = np.stack(vecs)
    pca = PCA(n_components=2,svd_solver='full')
    PCA_res = pca.fit_transform(vecs)
    # XY_range = (np.amin(PCA_res), np.amax(PCA_res))
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

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

    plt.scatter(PCA_res[:,0], PCA_res[:,1], s=s)

    if labels != None:
        new_texts = [plt.text(x_, y_, text, fontsize=label_font_size, color="black") for x_, y_, text in zip(PCA_res[:,0], PCA_res[:,1], labels)]
        num = adjust_text(new_texts, 
            only_move={'text': 'xy', "objects": "xy", "points": "xy"},
            arrowprops=dict(arrowstyle='-', linestyle="-.", color='silver',lw=arrow_lw),
            precision=0.0001)

    if xy_title != None:
        plt.xlabel(xy_title[0], fontsize=xy_title_font_size)
        plt.ylabel(xy_title[1], fontsize=xy_title_font_size)

    ax.spines['bottom'].set_linewidth(splines_lw)
    ax.spines['left'].set_linewidth(splines_lw)
    ax.spines['right'].set_linewidth(splines_lw)
    ax.spines['top'].set_linewidth(splines_lw)

    plt.xticks(fontsize=xy_ticks_font_size)
    plt.yticks(fontsize=xy_ticks_font_size)

    # plt.xlim = XY_range
    # plt.ylim = XY_range
    plt.show()
    if save_path != None:
        plt.savefig(save_path, dpi=dpi)

def CA_2D_plot(vecs_file_path, figsize, s=8, labels=None, label_font_size=16, xy_title_font_size=28, xy_ticks_font_size=14, splines_lw=4, arrow_lw=1, xy_title=None, xy_lim=None, xy_majoy_locator=None, xy_equal=True, save_path=None, dpi=600):
    vecs = utils.load_result(vecs_file_path)
    vecs = np.stack(vecs)
    ca = CA(n_components=2, n_iter=100, copy=True, check_input=True, engine='sklearn')
    CA_res = ca.fit_transform(vecs).row_coordinates(vecs)
    # XY_range = (np.amin(PCA_res), np.amax(PCA_res))
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

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

    plt.scatter(CA_res[:,0], CA_res[:,1], s=s)

    if labels != None:
        new_texts = [plt.text(x_, y_, text, fontsize=label_font_size, color="black") for x_, y_, text in zip(CA_res[:,0], CA_res[:,1], labels)]
        num = adjust_text(new_texts, 
            only_move={'text': 'xy', "objects": "xy", "points": "xy"},
            arrowprops=dict(arrowstyle='-', linestyle="-.", color='silver',lw=arrow_lw),
            precision=0.0001)

    if xy_title != None:
        plt.xlabel(xy_title[0], fontsize=xy_title_font_size)
        plt.ylabel(xy_title[1], fontsize=xy_title_font_size)

    ax.spines['bottom'].set_linewidth(splines_lw)
    ax.spines['left'].set_linewidth(splines_lw)
    ax.spines['right'].set_linewidth(splines_lw)
    ax.spines['top'].set_linewidth(splines_lw)

    plt.xticks(fontsize=xy_ticks_font_size)
    plt.yticks(fontsize=xy_ticks_font_size)

    # plt.xlim = XY_range
    # plt.ylim = XY_range
    plt.show()
    if save_path != None:
        plt.savefig(save_path, dpi=dpi)
