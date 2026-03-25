import matplotlib.pyplot as plt
import numpy as np
import csv

# File path
FILE_PATH = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Reports and Results/DNNplot Data and Plots/20250502 Celiac 200200 without TCC DNNplot data.tsv"
#FILE_PATH = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Reports and Results/DNNplot Data and Plots/20250502 Celiac 200200 full DNNplot data.tsv"
#FILE_PATH = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Reports and Results/DNNplot Data and Plots/20250411 CRC 200200 without TCC DNNplot data.tsv"
# Data file format - 2 columns, tab separated, first column is actual (-1 or 1), second column is prediction (-1 to 1 decimal)
OUTPUT_FILE_PATH = FILE_PATH.rsplit('.', 1)[0] + '.png'
#OUTPUT_FILE_PATH = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Reports and Results/DNNplot Data and Plots/20250411 SIBO200200-full-DNNplot-data.png"
THRESHOLD_CRITERION_VALUE = -0.316
EXPECTED_INPUT_ROWS = 373
TITLE_STRING="Celiac 200/200 Model"
#SUBTITLE_STRING="Full Data Set"
SUBTITLE_STRING="Excluding Low Confidence Results"

# Constants
DPI =  96 * 2  # Resolution
FIG_WIDTH = 8.5  # Inches
FIG_HEIGHT = 11
RECT_HEIGHT = 0.30  # Inches
TRIANGLE_SIZE = 0.01  # Inches 0.03

# Read data from file
data = []
#with open(FILE_PATH, "r") as file:
#    delimiter = "," if "," in file.readline() else "\t"
#    file.seek(0)  # Reset read position
#    reader = csv.reader(file, delimiter=delimiter)
#    Example Data
#     -1    -0.95   (tn - green, top, left)
#     -1	0.95    (fp - green, bottom, right)
#     1	    0.95    (tp - red, top, right)
#     1	    -0.95   (fn - red, bottom, left)



with open(FILE_PATH, "r") as file:
    delimiter = "," if "," in file.readline() else "\t"
    file.seek(0)  # Reset read position
    reader = csv.reader(file, delimiter=delimiter)
    line_count = 0
    for row in reader:
        line_count += 1  # Track number of lines read
        #print(f"Reading line {line_count}: {row}")
        try:
            prediction = float(row[1])   # Between -1 and 1
            actual = int(row[0])  # -1 or 1
            if actual in [-1, 1] and -1 <= prediction <= 1:  # Ensure valid input
                data.append((actual, prediction))
            else:
                raise ValueError
        except ValueError as e:
            print(f"Invalid row at line {line_count}: {row}")
            print(f"Error: {e}")
            #continue  # Skip invalid rows
            exit(1)
        except Exception as e:
            print(f"Unexpected error at line {line_count}: {row}")
            print(f"Error: {e}")
            #continue  # Skip other exceptions
            exit(2)
    print(f"Read {line_count} lines from file {FILE_PATH}. Last line {line_count}: {row}")

    if line_count != EXPECTED_INPUT_ROWS:
        print(f"Expected {EXPECTED_INPUT_ROWS} lines, but read {line_count}.")
        exit(3)



# Count stacking for each (X, Y) pair
stacking = {}
if len(data) != EXPECTED_INPUT_ROWS:
    print(f"Error: Expected {EXPECTED_INPUT_ROWS} rows but found {len(data)} rows in the data")
    exit(4)

data_count=0
for actual, prediction in data:
    data_count += 1
    stacking[(actual, prediction)] = stacking.get((actual, prediction), 0) + 1
    print(f"Prediction: {prediction}, Actual: {actual}, Count: {stacking[(actual, prediction)]}", flush=True)

if data_count != EXPECTED_INPUT_ROWS:
    print(f"Error: We have {len(data)} rows in the data array, but processed only {data_count} rows from the data")
    exit(5)


# Set up plot
fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.2, 1.2)
ax.axis("off")

# Add Title
threshold_display_value = "|\n" + str(THRESHOLD_CRITERION_VALUE) + "\n|"

ax.text(0, 1.0, TITLE_STRING + "\n" + SUBTITLE_STRING, fontsize=16, fontweight="regular", ha="center")
ax.text(THRESHOLD_CRITERION_VALUE, -0.1, threshold_display_value, fontsize=18, fontweight="regular", ha="center")
ax.text(-1, -0.04, "-1 (disease absent)", fontsize=10, fontweight="regular", ha="left")
ax.text(1, -0.04, "(disease present) +1", fontsize=10, fontweight="regular", ha="right")

#ax.text(-1, -1, """
#The placement of the triangle on the plot represents the result that the Luventix model produced.
#The triangle color indicates that the sample was from a disease positive patient (red) or a control (green).
#The colored bar represents the confidence of the match between the sample and the model.
#The bar goes from disease absent to the left in green to disease present to the right in red.
#Triangles are above the bar, if they were correctly classified and below the bar if they were misclassified.
#A red triangle below the bar is a False Negative, a green triangle below the bar is a False Positive.
#Red above the bar is a True Positive, Green above the bar is a True Negative.
#Triangles are stacked to show how many tests returned the same absolute model output value.
#The test results are between -1 and 1. A -1 would be a "perfect" match to the modeled disease absent
#metabolic profiles, and +1 would indicate a "perfect" match to the modeled disease present metabolic profiles.
#""", fontsize=8, ha="left")



# Draw gradient X-axis (Green → Red, 0 → 1)
gradient = np.linspace(0, 1, 256).reshape(1, -1)
ax.imshow(gradient, aspect="auto", extent=(-1, 1, -RECT_HEIGHT / 2, RECT_HEIGHT / 2), cmap="RdYlGn_r")  # Corrected colormap

# Draw triangles
tp_count = 0
tn_count = 0
fp_count = 0
fn_count = 0
for actual, prediction in data:
    stack_level = stacking[(actual, prediction)] - 1
    stacking[(actual, prediction)] -= 1  # Reduce count for stacking effect

    # Map prediction values to actual position
    x_pos = prediction  # The decimal prediction value directly determines the actual position

    # Determine triangle color (based on prediction value)
    triangle_color = "green" if actual == -1 else "red"

    # Determine Y position for stacking
    triangle_y = (RECT_HEIGHT / 1.8) + (TRIANGLE_SIZE * stack_level)

    # Above or Below logic
    #threshold = 0 # this is for a perfectly balanced model

    threshold = THRESHOLD_CRITERION_VALUE # this is for criterion from medcalc
    classified_as = "NOT CLASSIFIED"
    print(f"{actual}, {prediction}, {threshold}", flush=True)
    if (actual == 1 and prediction >= threshold) or (actual == -1 and prediction < threshold):
        #  Both positive or both negative -  Above the axis
        triangle_points = [[x_pos, triangle_y], [x_pos - 0.05, triangle_y + 0.1], [x_pos + 0.05, triangle_y + 0.1]]
        if (actual == 1 and prediction >= threshold):
            classified_as = "True Positive"
            tp_count += 1
        if (actual == -1 and prediction < threshold):
            classified_as = "True Negative"
            tn_count += 1
    else:
        if (actual == -1 and prediction >= threshold):
            classified_as = "False Positive"
            fp_count += 1
        if (actual == 1 and prediction < threshold):
            classified_as = "False Negative"
            fn_count += 1
        print(f"Below the line: {actual}, {prediction}, {classified_as}, {threshold}", flush=True)
        print()
        # One negative, one positive - Below the axis
        triangle_y *= -1
        triangle_points = [[x_pos, triangle_y], [x_pos - 0.05, triangle_y - 0.1], [x_pos + 0.05, triangle_y - 0.1]]
        #switch the colors on the bottom to indicate error
        #if triangle_color == "green":
        #    triangle_color = "red"
        #else:
        #    triangle_color = "green"

    ax.add_patch(plt.Polygon(triangle_points, color=triangle_color))

#lables in the four corners
ax.text(0.975, 1.23, "Tp=" + str(tp_count), color="green", fontsize=10, fontweight="regular", ha="right")
ax.text(-0.93, 1.23, "Tn=" + str(tn_count), color="green", fontsize=10, fontweight="regular", ha="right")
ax.text(-0.93, -0.4, "Fn=" + str(fn_count), color="brown", fontsize=10, fontweight="regular", ha="right")
ax.text(0.975, -0.4, "Fp=" + str(fp_count), color="brown", fontsize=10, fontweight="regular", ha="right")

#Print Stats:
print(f"Tn: {tn_count}, Tp: {tp_count}, Fn: {fn_count}, Fp: {fp_count}, Total: {tn_count+tp_count+fn_count+fp_count}", flush=True)
# Save plot
plt.savefig(OUTPUT_FILE_PATH, bbox_inches="tight", dpi=DPI)
plt.show()