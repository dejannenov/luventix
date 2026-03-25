# /app/chromatography/peak_finder.py

import pandas as pd
import numpy as np
import argparse
from typing import Tuple, List


def load_chromatography_data(filepath: str) -> pd.DataFrame:
    """
    Load chromatography data from a TSV file, removing the first 4 metadata columns.
    """
    print("Loading data.")
    # with first rows as a header and first three columns strings
    df_raw = pd.read_csv(filepath, sep="\t", header=None, dtype={1: str, 2: str, 3: str})
    print("Removing first 3 columns.")
    df_data = df_raw.iloc[:, 3:]

    print("MaxRows = ",  df_data.shape[0])
    print("Number of columns:", df_data.shape[1])


    return df_data


def find_peak_x_in_range(
        df: pd.DataFrame,
        x_range: Tuple[int, int],
        y_rows: List[int]
) -> float:
    """
    Find the x-position of the peak within a given x range and selected y-rows.
    """
    x_vals = df.iloc[0].astype(int).values
    min_x, max_x = x_range

    #print("x-values being checked:", x_vals)
    #print("x_range:", x_range)
    #print("min(x_values):", min(x_vals), "max(x_values):", max(x_vals))

    x_mask = (x_vals >= min_x) & (x_vals <= max_x)
    if not np.any(x_mask):
        raise ValueError("No x-values found in the specified range.")

    selected_y_data = df.iloc[y_rows].astype(int).values[:, x_mask]
    mean_y = selected_y_data.mean(axis=0)
    peak_index = np.argmax(mean_y)
    peak_x = x_vals[x_mask][peak_index]

    return peak_x

def df_shift(df, row_idx, shift):
    """
    Shift the y-values in row `row_idx` of DataFrame `df` by `shift` positions.
    Positive `shift` shifts right (prepend zeros), negative shifts left (append zeros).
    Values shifted out are dropped; new values are filled with 0.
    Only applies to columns containing the y-values (not metadata).
    """
    # Get the row as a numpy array
    row = df.iloc[row_idx].values.copy()
    n = len(row)
    shifted_row = np.zeros_like(row)
    if shift > 0:
        # Shift right
        shifted_row[shift:] = row[:n-shift]
        shifted_row[:shift] = 0
    elif shift < 0:
        # Shift left
        shifted_row[:shift] = row[-shift:]
        shifted_row[shift:] = 0
    else:
        shifted_row = row
    # Assign back to DataFrame
    df.iloc[row_idx] = shifted_row
    return df



def main():

    print("\n\n\nStarting...")
    df = load_chromatography_data("C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Data/Raw Data - All Files/Full Full Data Set/20250616-luv-align-data.tsv")

    #### Sibo-5050-qc rows 201-208 Peak x-position: 10169 y_rows = [201,202,203,204,205,206,207,208]
    ## sibo-50 rows 558-607  Peak x-position: 10165   y_rows = [558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607]
    ## sibo-50-controls rows 608-657  Peak x-position: 10165   y_rows = [608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657]

    ## sibo-150-qc-1 rows 188-195 Peak x-position: 10040 y_rows = [188, 189, 190, 191, 192, 193, 194, 195]
    ## SIBO-150 rows 958-1107 Peak x-position: 10040 y_rows = [958,959,960,961,962,963,964,965,966,967,968,969,970,971,972,973,974,975,976,977,978,979,980,981,982,983,984,985,986,987,988,989,990,991,992,993,994,995,996,997,998,999,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029,1030,1031,1032,1033,1034,1035,1036,1037,1038,1039,1040,1041,1042,1043,1044,1045,1046,1047,1048,1049,1050,1051,1052,1053,1054,1055,1056,1057,1058,1059,1060,1061,1062,1063,1064,1065,1066,1067,1068,1069,1070,1071,1072,1073,1074,1075,1076,1077,1078,1079,1080,1081,1082,1083,1084,1085,1086,1087,1088,1089,1090,1091,1092,1093,1094,1095,1096,1097,1098,1099,1100,1101,1102,1103,1104,1105,1106,1107]

    # celiac-5050-qc rows 24-31 Peak x-position: 10185 y_rows = [36, 37, 38]
    # celiac-50 rows 458-506 Peak x-position: 10185 y_rows = [458, 459, 460, 470, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506]
    ## celiac-50-controls rows 508-557 Peak x-position: 10184 y_rows = [508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557]

    # crohns-150-cal rows 126-132 Peak x-position: 10109 y_rows = [126, 127, 128, 129, 130, 131, 132]
    # crohns-5050-cal row 160-167 Peak x-position: 10222 y_rows = [160, 161, 162, 163, 164, 165, 166, 167]
    # crohns-5050-qc rows 171-174 Peak x-position: 10225 y_rows = [171, 172, 173, 174]
    ## crohns-50-controls rows 408-457 Peak x-position: 10217 y_rows = [408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457]

    #crc-5050-cal rows 63-70 Peak x-position: 10250 y_rows = [63, 64, 65, 66, 67, 68, 69, 70]
    ##crc-50-controls rows 308-357  Peak x-position: 10250   y_rows = [308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357]



    x_range = (9900, 10250)
    y_rows = [201,202,203,204,205,206,207,208]
    peak = find_peak_x_in_range(df, x_range, y_rows)
    print("Average Peak x-position:", peak)

    for y in y_rows:
        peak = find_peak_x_in_range(df, x_range, [y])
        print(f"Peak x-position for y={y}: {peak}")


    # now created a shifted matrix
    df_shifted = df
    #df_shifted = df_shift(df_shifted, row_idx, shift)

    print("End.\n")

    #parser = argparse.ArgumentParser(description="Chromatography Peak Finder")
    #parser.add_argument("file", type=str, help="Path to TSV file")
    #parser.add_argument("--x_min", type=float, required=True, help="Minimum x value of range")
    #parser.add_argument("--x_max", type=float, required=True, help="Maximum x value of range")
    #parser.add_argument("--y_rows", type=int, nargs="+", required=True, help="List of y row indices")
    #args = parser.parse_args()
    #df = load_chromatography_data(args.file)
    #x_range = (args.x_min, args.x_max)
    #peak = find_peak_x_in_range(df, x_range, args.y_rows)

    print(f"Peak x-position: {peak}")


if __name__ == "__main__":
    main()
