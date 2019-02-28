from .general import *
from .ignore_warnings import *

import IPython
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from easydict import EasyDict
from tqdm import tqdm_notebook
import shutil
import datetime

## File utilities

def ensure_folder(folder):
    """Make sure a folder exists."""
    Path(folder).mkdir(exist_ok=True, parents=True)

def ensure_delete(folder_or_file):
    anything = Path(folder_or_file)
    if anything.is_dir():
        shutil.rmtree(str(folder_or_file))
    elif anything.exists():
        anything.unlink()

def copy_file(src, dst):
    """Copy source file to destination file."""
    assert Path(src).is_file()
    shutil.copy(str(src), str(dst))

def _copy_any(src, dst, symlinks):
    if Path(src).is_dir():
        if Path(dst).is_dir():
            dst = Path(dst)/Path(src).name
        assert not Path(dst).exists()
        shutil.copytree(src, dst, symlinks=symlinks)
    else:
        copy_file(src, dst)

def copy_any(src, dst, symlinks=True):
    """Copy any file or folder recursively.
    Source file can be list/array of files.
    """
    do_list_item(_copy_any, src, dst, symlinks)

def do_list_item(func, src, *prms):
    if isinstance(src, (list, tuple, np.ndarray)):
        result = True
        for element in src:
            result = do_list_item(func, element, *prms) and result
        return result
    else:
        return func(src, *prms)

def _move_file(src, dst):
    shutil.move(str(src), str(dst))

def move_file(src, dst):
    """Move source file to destination file/folder.
    Source file can be list/array of files.
    """
    do_list_item(_move_file, src, dst)

def symlink_file(fromfile, tofile):
    """Make fromfile's symlink as tofile."""
    Path(tofile).symlink_to(fromfile)

def make_copy_to(dest_folder, files, n_sample=None, operation=copy_file):
    """Do file copy like operation from files to dest_folder.
    
    If n_sample is set, it creates symlinks up to number of n_sample files.
    If n_sample is greater than len(files), symlinks are repeated twice or more until it reaches to n_sample.
    If n_sample is less than len(files), n_sample symlinks are created for the top n_sample samples in files."""
    dest_folder.mkdir(exist_ok=True, parents=True)
    if n_sample is None:
        n_sample = len(files)

    _done = False
    _dup = 0
    _count = 0
    while not _done: # yet
        for f in files:
            f = Path(f)
            name = f.stem+('_%d'%_dup)+f.suffix if 0 < _dup else f.name
            to_file = dest_folder / name
            operation(f, to_file)
            _count += 1
            _done = n_sample <= _count
            if _done: break
        _dup += 1
    print('Now', dest_folder, 'has', len(list(dest_folder.glob('*'))), 'files.')

## Log utilities

import logging
_loggers = {}
def get_logger(name=None, level=logging.DEBUG, format=None, print=True, output_file=None):
    """One liner to get logger.
    See test_log.py for example.
    """
    name = name or __name__
    if _loggers.get(name):
        return _loggers.get(name)
    else:
        log = logging.getLogger(name)
    formatter = logging.Formatter(format or '%(asctime)s %(name)s %(funcName)s [%(levelname)s]: %(message)s')
    def add_handler(handler):
        handler.setFormatter(formatter)
        handler.setLevel(level)
        log.addHandler(handler)
    if print:
        add_handler(logging.StreamHandler())
    if output_file:
        ensure_folder(Path(output_file).parent)
        add_handler(logging.FileHandler(output_file))
    log.setLevel(level)
    log.propagate = False
    _loggers[name] = log
    return log

## Multi process utilities

def caller_func_name(level=2):
    """Return caller function name."""
    return sys._getframe(level).f_code.co_name

def _file_mutex_filename(filename):
    return filename or '/tmp/'+Path(caller_func_name(level=3)).stem+'.lock'

def lock_file_mutex(filename=None):
    """Lock file mutex (usually placed under /tmp).
    Note that filename will be created based on caller function name.
    """
    filename = _file_mutex_filename(filename)
    with open(filename, 'w') as f:
        f.write('locked at {}'.format(datetime.datetime.now()))
def release_file_mutex(filename=None):
    """Release file mutex."""
    filename = _file_mutex_filename(filename)
    ensure_delete(filename)

def is_file_mutex_locked(filename=None):
    """Check if file mutex is locked or not."""
    filename = _file_mutex_filename(filename)
    return Path(filename).exists()

## Date utilities

def str_to_date(text):
    if '/' in text:
        temp_dt = datetime.datetime.strptime(text, '%Y/%m/%d')
    else:
        temp_dt = datetime.datetime.strptime(text, '%Y-%m-%d')
    return datetime.date(temp_dt.year, temp_dt.month, temp_dt.day)

# def get_week_start_end_dates(week_no:int, year=None) -> [datetime.datetime, datetime.datetime]:
#     """Get start and end date of an ISO calendar week.
#     ISO week starts on Monday, and ends on Sunday.
    
#     Arguments:
#         week_no: ISO calendar week number
#         year: Year to calculate, None will set this year

#     Returns:
#         [start_date:datetime, end_date:datetime]
#     """
#     if not year:
#         year, this_week, this_day = datetime.datetime.today().isocalendar()
#     start_date = datetime.datetime.strptime(f'{year}-W{week_no:02d}-1', "%G-W%V-%u").date()
#     end_date = datetime.datetime.strptime(f'{year}-W{week_no:02d}-7', "%G-W%V-%u").date()
#     return [start_date, end_date]

def get_this_week_no():
    """Get ISO calendar week no of today."""
    return datetime.datetime.today().isocalendar()[1]

## List utilities

def write_text_list(textfile, a_list):
    """Write list of str to a file with new lines."""
    with open(textfile, 'w') as f:
        f.write('\n'.join(a_list)+'\n')

def read_text_list(filename) -> list:
    """Read text file splitted as list of texts, stripped."""
    with open(filename) as f:
        lines = f.read().splitlines()
        return [l.strip() for l in lines]

from itertools import chain
def flatten_list(lists):
    return list(chain.from_iterable(lists))

# Thanks to https://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
def all_elements_are_identical(iterator):
    """Check all elements in iterable like list are identical."""
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)

## Text utilities

# Thanks to https://github.com/dsindex/blog/wiki/%5Bpython%5D-difflib,-show-differences-between-two-strings
import difflib
def show_text_diff(text, n_text):
    """
    http://stackoverflow.com/a/788780
    Unify operations between two compared strings seqm is a difflib.
    SequenceMatcher instance whose a & b are strings
    """
    seqm = difflib.SequenceMatcher(None, text, n_text)
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            pass # output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append("<INS>" + seqm.b[b0:b1] + "</INS>")
        elif opcode == 'delete':
            output.append("<DEL>" + seqm.a[a0:a1] + "</DEL>")
        elif opcode == 'replace':
            # seqm.a[a0:a1] -> seqm.b[b0:b1]
            output.append("<REPL>" + seqm.b[b0:b1] + "</REPL>")
        else:
            raise RuntimeError
    return ''.join(output)

import unicodedata
def unicode_visible_width(unistr):
    """Returns the number of printed characters in a Unicode string."""
    return sum([1 if unicodedata.east_asian_width(char) in ['N', 'Na'] else 2 for char in unistr])

## Pandas utilities

def df_to_csv_excel_friendly(df, filename, **args):
    """df.to_csv() to be excel friendly UTF-8 handling."""
    df.to_csv(filename, encoding='utf_8_sig', **args)

def df_merge_update(df_list_or_org_file, opt_joining_file=None):
    """Merge data frames while update duplicated index with following (joining) row.
    
    Usages:
        - df_merge_update([df1, df2, ...]) merges dfs in list.
        - df_merge_update(df1, df2) merges df1 and df2.
    """
    if opt_joining_file is not None:
        df_list = [df_list_or_org_file, opt_joining_file]
    else:
        df_list = df_list_or_org_file

    master = df_list[0]
    for df in df_list[1:]:
        tmp_df = pd.concat([master, df])
        master = tmp_df[~tmp_df.index.duplicated(keep='last')].sort_index()
    return master

def df_select_by_keyword(source_df, keyword, search_columns=None, as_mask=False):
    """Select data frame rows by a search keyword.
    Any row will be selected if any of its search columns contain the keyword.
    
    Returns:
        New data frame where rows have the keyword,
        or mask if as_mask is True.
    """
    search_columns = search_columns or source_df.columns
    masks = np.column_stack([source_df[col].str.contains(keyword, na=False) for col in search_columns])
    mask = masks.any(axis=1)
    if as_mask:
        return mask
    return source_df.loc[mask]

def df_select_by_keywords(source_df, keys_cols, and_or='or', as_mask=False):
    """Multi keyword version of df_select_by_keyword.

    Arguments:
        key_cols: dict defined as `{'keyword1': [search columns] or None, ...}`
    """
    masks = []
    for keyword in keys_cols:
        columns = keys_cols[keyword]
        mask = df_select_by_keyword(source_df, keyword, search_columns=columns, as_mask=True)
        masks.append(mask)
    mask = np.column_stack(masks).any(axis=1) if and_or == 'or' else \
           np.column_stack(masks).all(axis=1)
    if as_mask:
        return mask
    return source_df.loc[mask]

def df_str_replace(df, from_strs, to_str):
    """Apply str.replace to entire DataFrame inplace."""
    for i, row in df.iterrows():
        df.ix[i] = df.ix[i].str.replace(from_strs, to_str)

def df_cell_str_replace(df, from_str, to_str):
    """Replace cell string with new string if entire string matches."""
    for i, row in df.iterrows():
        for c in df.columns:
            df.at[i, c] = to_str if str(df.at[i, c]) == from_str else df.at[i, c]

_EXCEL_LIKE = ['.csv', '.xls', '.xlsx', '.xlsm']
def is_excel_file(filename):
    # not accepted if suffix == '.csv': return True
    return Path(filename).suffix.lower() in _EXCEL_LIKE

def is_csv_file(filename):
    return Path(filename).suffix.lower() == '.csv'

def pd_read_excel_keep_dtype(io, **args):
    """pd.read_excel() wrapper to do as described in pandas document:
    '... preserve data as stored in Excel and not interpret dtype'

    Details:
        - String '1' might be loaded as int 1 by pd.read_excel(file).
        - By setting `dtype=object` it will preserve it as string '1'.
    """
    return pd.read_excel(io, dtype=object, **args)

def pd_read_csv_as_str(filename, **args):
    """pd.read_csv() wrapper to preserve data type = str"""
    return pd.read_csv(filename, dtype=object, **args)

def df_load_excel_like(filename, preserve_dtype=True, **args):
    """Load Excel like files. (csv, xlsx, ...)"""
    if is_csv_file(filename):
        if preserve_dtype:
            return pd_read_csv_as_str(filename, **args)
        return pd.read_csv(filename, **args)
    if preserve_dtype:
        return pd_read_excel_keep_dtype(filename, **args)
    return pd.read_excel(filename, **args)

import codecs
def df_read_sjis_csv(filename, **args):
    """Read shift jis Japanese csv file.
    Thanks to https://qiita.com/niwaringo/items/d2a30e04e08da8eaa643
    """
    with codecs.open(filename, 'r', 'Shift-JIS', 'ignore') as file:
        return pd.read_table(file, delimiter=',', **args)

## Dataset utilities

from imblearn.over_sampling import RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler

def flatten_y_if_onehot(y):
    """De-one-hot y, i.e. [0,1,0,0,...] to 1 for all y."""
    return y if len(np.array(y).shape) == 1 else np.argmax(y, axis = -1)

def get_class_distribution(y):
    """Calculate number of samples per class."""
    # y_cls can be one of [OH label, index of class, class label name string]
    # convert OH to index of class
    y_cls = flatten_y_if_onehot(y)
    # y_cls can be one of [index of class, class label name]
    classset = sorted(list(set(y_cls)))
    sample_distribution = {cur_cls:len([one for one in y_cls if one == cur_cls]) for cur_cls in classset}
    return sample_distribution

def get_class_distribution_list(y, num_classes):
    """Calculate number of samples per class as list"""
    dist = get_class_distribution(y)
    assert(y[0].__class__ != str) # class index or class OH label only
    list_dist = np.zeros((num_classes))
    for i in range(num_classes):
        if i in dist:
            list_dist[i] = dist[i]
    return list_dist

def _balance_class(X, y, min_or_max, sampler_class, random_state):
    """Balance class distribution with sampler_class."""
    y_cls = flatten_y_if_onehot(y)
    distribution = get_class_distribution(y_cls)
    classes = list(distribution.keys())
    counts  = list(distribution.values())
    nsamples = np.max(counts) if min_or_max == 'max' \
          else np.min(counts)
    flat_ratio = {cls:nsamples for cls in classes}
    Xidx = [[xidx] for xidx in range(len(X))]
    sampler_instance = sampler_class(ratio=flat_ratio, random_state=random_state)
    Xidx_resampled, y_cls_resampled = sampler_instance.fit_sample(Xidx, y_cls)
    sampled_index = [idx[0] for idx in Xidx_resampled]
    return np.array([X[idx] for idx in sampled_index]), np.array([y[idx] for idx in sampled_index])

def balance_class_by_over_sampling(X, y, random_state=42):
    """Balance class distribution with imbalanced-learn RandomOverSampler."""
    return  _balance_class(X, y, 'max', RandomOverSampler, random_state)

def balance_class_by_under_sampling(X, y, random_state=42):
    """Balance class distribution with imbalanced-learn RandomUnderSampler."""
    return  _balance_class(X, y, 'min', RandomUnderSampler, random_state)

def df_balance_class_by_over_sampling(df, label_column, random_state=42):
    """Balance class distribution in DataFrame with imbalanced-learn RandomOverSampler."""
    X, y = list(range(len(df))), list(df[label_column])
    X, _ = balance_class_by_over_sampling(X, y, random_state=random_state)
    return df.iloc[X].sort_index()

def df_balance_class_by_under_sampling(df, label_column, random_state=42):
    """Balance class distribution in DataFrame with imbalanced-learn RandomUnderSampler."""
    X, y = list(range(len(df))), list(df[label_column])
    X, _ = balance_class_by_under_sampling(X, y, random_state=random_state)
    return df.iloc[X].sort_index()

## Visualization utilities

def _expand_labels_from_y(y, labels):
    """Make sure y is index of label set."""
    if labels is None:
        labels = sorted(list(set(y)))
        y = [labels.index(_y) for _y in y]
    return y, labels

def visualize_class_balance(title, y, labels=None, sorted=False):
    y, labels = _expand_labels_from_y(y, labels)
    sample_dist_list = get_class_distribution_list(y, len(labels))
    if sorted:
        items = list(zip(labels, sample_dist_list))
        items.sort(key=lambda x:x[1], reverse=True)
        sample_dist_list = [x[1] for x in items]
        labels = [x[0] for x in items]
    index = range(len(labels))
    fig, ax = plt.subplots(1, 1, figsize = (16, 5))
    ax.bar(index, sample_dist_list)
    ax.set_xlabel('Label')
    ax.set_xticks(index)
    ax.set_xticklabels(labels, rotation='vertical')
    ax.set_ylabel('Number of Samples')
    ax.set_title(title)
    fig.show()

from collections import OrderedDict
def print_class_balance(title, y, labels=None, sorted=False):
    y, labels = _expand_labels_from_y(y, labels)
    distributions = get_class_distribution(y)
    dist_dic = {labels[cls]:distributions[cls] for cls in distributions}
    if sorted:
        items = list(dist_dic.items())
        items.sort(key=lambda x:x[1], reverse=True)
        dist_dic = OrderedDict(items) # sorted(dist_dic.items(), key=...) didn't work for some reason...
    print(title, '=', dist_dic)
    zeroclasses = [label for i, label in enumerate(labels) if i not in distributions.keys()]
    if 0 < len(zeroclasses):
        print(' 0 sample classes:', zeroclasses)

from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score

def calculate_clf_metrics(y_true, y_pred, average='weighted'):
    """Calculate metrics: f1/recall/precision/accuracy.

    # Arguments
        y_true: GT, an index of label or one-hot encoding format.
        y_pred: Prediction output, index or one-hot.
        average: `average` parameter passed to sklearn.metrics functions.

    # Returns
        Four metrics: f1, recall, precision, accuracy.
    """
    y_true = flatten_y_if_onehot(y_true)
    y_pred = flatten_y_if_onehot(y_pred)
    if np.max(y_true) < 2 and np.max(y_pred) < 2:
        average = 'binary'

    f1 = f1_score(y_true, y_pred, average=average)
    recall = recall_score(y_true, y_pred, average=average)
    precision = precision_score(y_true, y_pred, average=average)
    accuracy = accuracy_score(y_true, y_pred)
    return f1, recall, precision, accuracy

def skew_bin_clf_preds(y_pred, binary_bias=None, logger=None):
    """Apply bias to prediction results for binary classification.
    Calculated as follows.
        p(y=1) := p(y=1) ^ binary_bias
        p(y=0) := 1 - p(y=0)
    0 < binary_bias < 1 will be optimistic with result=1.
    Inversely, 1 < binary_bias will make results pesimistic.
    """
    _preds = np.array(y_pred.copy())
    if binary_bias is not None:
        ps = np.power(_preds[:, 1], binary_bias)
        _preds[:, 1] = ps
        _preds[:, 0] = 1 - ps
        logger = get_logger() if logger is None else logger
        logger.info(f' @skew{"+" if binary_bias >= 0 else ""}{binary_bias}')
    return _preds

def print_clf_metrics(y_true, y_pred, average='weighted', binary_bias=None, title_prefix='', logger=None):
    """Calculate and print metrics: f1/recall/precision/accuracy.
    See calculate_clf_metrics() and skew_bin_clf_preds() for more detail.
    """
    # Add bias if binary_bias is set
    _preds = skew_bin_clf_preds(y_pred, binary_bias, logger=logger)
    # Calculate metrics
    f1, recall, precision, acc = calculate_clf_metrics(y_true, _preds, average=average)
    logger = get_logger() if logger is None else logger
    logger.info('{0:s}F1/Recall/Precision/Accuracy = {1:.4f}/{2:.4f}/{3:.4f}/{4:.4f}' \
          .format(title_prefix, f1, recall, precision, acc))

# Thanks to https://qiita.com/knknkn1162/items/be87cba14e38e2c0f656
def plt_japanese_font_ready():
    """Set font family with Japanese fonts.
    
    # How to install fonts:
        wget https://ipafont.ipa.go.jp/old/ipafont/IPAfont00303.php
        mv IPAfont00303.php IPAfont00303.zip
        unzip -q IPAfont00303.zip
        sudo cp IPAfont00303/*.ttf /usr/share/fonts/truetype/
    """
    plt.rcParams['font.family'] = 'IPAPGothic'

def plt_looks_good():
    """Plots will be looks good (at least to me)."""
    plt.rcParams["figure.figsize"] = [16, 10]
    plt.rcParams['font.size'] = 14
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10

# Thanks to http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html#sphx-glr-auto-examples-model-selection-plot-confusion-matrix-py
import itertools
from sklearn.metrics import confusion_matrix

def plot_confusion_matrix(y_test, y_pred, classes,
                          normalize=True,
                          title=None,
                          cmap=plt.cm.Blues):
    """Plot confusion matrix."""
    po = np.get_printoptions()
    np.set_printoptions(precision=2)

    y_test = flatten_y_if_onehot(y_test)
    y_pred = flatten_y_if_onehot(y_pred)
    cm = confusion_matrix(y_test, y_pred)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        if title is None: title = 'Normalized confusion matrix'
    else:
        if title is None: title = 'Confusion matrix (not normalized)'

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    np.set_printoptions(**po)
