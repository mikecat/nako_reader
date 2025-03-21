import sys

time_warp_limit = None
if len(sys.argv) > 1:
    time_warp_limit = float(sys.argv[1])

prev_status = None
prev_status_no_notch = None
pending_status_no_notch = None
pending_status = None

prev_time_str = None
prev_time = None
prev_distance = None
prev_speed = "0.0"

def emit_status(status):
    global prev_time_str, prev_time, prev_distance, prev_speed
    time_str, distance = status.split("\t")[0:2]
    time = float(time_str)
    distance = float(distance)
    if prev_time is not None and time_warp_limit is not None:
        if time > prev_time or prev_time - time > time_warp_limit:
            return
    speed = prev_speed
    if prev_time is not None and time_str != prev_time_str:
        speed = "%.1f" % ((prev_distance - distance) / (prev_time - time) * 3.6)
    prev_time_str = time_str
    prev_time = time
    prev_distance = distance
    prev_speed = speed
    print(status + "\t" + speed)

for line in sys.stdin.readlines():
    line = line.rstrip()
    line_data = line.split("\t")
    if len(line_data) != 5:
        print(line)
    elif line_data[4] == "notch":
        print("\t".join(["time [s]", line_data[2], line_data[3], line_data[4], "true_speed [km/h]"]))
    else:
        time_data = line_data[1].split(":")
        if len(time_data) != 3:
            print(line)
        else:
            m, s, cs = time_data
            if m[0] == "-":
                time_str = str(int(m) * 60 - int(s)) + "." + cs
            else:
                time_str = str(int(m) * 60 + int(s)) + "." + cs
            status_no_notch = "\t".join([time_str, line_data[2], line_data[3]])
            notch = line_data[4]
            status = status_no_notch + "\t" + notch
            if status != prev_status:
                if notch != "?":
                    if pending_status_no_notch is not None and pending_status_no_notch != status_no_notch:
                        emit_status(pending_status)
                    emit_status(status)
                    pending_status_no_notch = None
                    pending_status = None
                else:
                    if status_no_notch != prev_status_no_notch:
                        if pending_status is not None:
                            emit_status(pending_status)
                        pending_status_no_notch = status_no_notch
                        pending_status = status
                prev_status = status
                prev_status_no_notch = status_no_notch

if pending_status is not None:
    print(pending_status)
