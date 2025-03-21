import sys
import os
import json
from PIL import Image

args = sys.argv[1:]
model_file = os.path.join(os.path.dirname(__file__), "model.json")
print_header = False
serial_mode = False
help_requested = False

while len(args) > 0:
    if args[0] == "--model" and len(args) > 1:
        model_file = args[1]
        args = args[1:]
    elif args[0] == "--header":
        print_header = True
    elif args[0] == "--serial":
        serial_mode = True
    elif args[0] == "--help":
        help_requested = True
    else:
        break
    args = args[1:]

if len(args) == 0 or help_requested:
    print("Usage: nako_reader.py [options] file [file...]")
    print("")
    print("options:")
    print("  --model <file> : specify model file")
    print("  --header       : print data header line")
    print("  --serial       : use serial file process mode")
    print("  --help         : print this help")
    sys.exit(0)

with open(model_file) as f:
    model = json.load(f)

if print_header:
    print("file\ttime\tdistance [m]\tspeed [km/h]\tnotch")

def read_puttern(image, threshold, putterns):
    number_table = model["common"]["number_table"]
    for puttern in putterns:
        result = ""
        for query in puttern:
            if query["type"] == "7seg":
                if "segments" in query:
                    segments = query["segments"]
                else:
                    segments = {}
                    segments["a"] = [query["xs"][1], query["ys"][0]]
                    segments["b"] = [query["xs"][2], query["ys"][1]]
                    segments["c"] = [query["xs"][2], query["ys"][3]]
                    segments["d"] = [query["xs"][1], query["ys"][4]]
                    segments["e"] = [query["xs"][0], query["ys"][3]]
                    segments["f"] = [query["xs"][0], query["ys"][1]]
                    segments["g"] = [query["xs"][1], query["ys"][2]]
                on_list = ""
                for k in "abcdefg":
                    if image.getpixel(tuple(segments[k])) >= threshold:
                        on_list += k
                if on_list in number_table:
                    result += number_table[on_list]
                else:
                    result = None
                    break
            elif query["type"] == "fixed":
                for white_pixel in query["whites"]:
                    if image.getpixel(tuple(white_pixel)) < threshold:
                        result = None
                        break
                for black_pixel in query["blacks"]:
                    if image.getpixel(tuple(black_pixel)) >= threshold:
                        result = None
                        break
                if result is None:
                    break
                result += query["char"]
        if result is not None:
            return result
    return None

def read_notch(image, threshold, notch_model):
    result = None
    x = notch_model["x"]
    for setting in notch_model["settings"]:
        yes = True
        for y in setting["ys"]:
            if image.getpixel((x, y)) < threshold:
                yes = False
                break
        if yes:
            if result is not None:
                return None
            result = setting["name"]
    return result

def process(file):
    try:
        image = Image.open(file).convert("L")
        for threshold in model["common"]["thresholds"]:
            time = read_puttern(image, threshold, model["time"]["putterns"])
            if time is None:
                continue
            distance = read_puttern(image, threshold, model["distance"]["putterns"])
            if distance is None:
                continue
            speed = read_puttern(image, threshold, model["speed"]["putterns"])
            if speed is None:
                continue
            notch = read_notch(image, threshold, model["notch"])
            if notch is None:
                notch = "?"
            print("\t".join([file, time, distance, speed, notch]))
            return
        raise Exception("failed to read status")
    except Exception as e:
        sys.stderr.write("error in processing " + file + ": ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")

for file in args:
    if serial_mode:
        i = 1
        while True:
            current_file = file % i
            if os.path.isfile(current_file):
                process(current_file)
            else:
                break
            i += 1
    else:
        process(file)
