def get_card():
    att_record = []
    len_ = len(initial_record)
    pop_list = []        
    for i in range(len_):
        e = initial_record_origin[i]
        if e[2]<start_date:
            pop_list.append(e)
            continue
        else:
            if e[2]<=end_date:
                att_record.append(i)
                e[4] +=1
            else:
                break
    for e in pop_list:
        initial_record.remove(e)
    return att_record
            
    dur1 = abs(start_date-initial_record[0][2])
    dur2 = abs(initial_record[-1][2]-end_date)
    att_record = []
    if dur2<dur1:
        len_ = len(initial_record)
        for i in range(len_):
            e = initial_record[len_-i-1]
            if e[2]>end_date:
                continue
            else:
                if e[2]>=start_date:
                    att_record.append(e)
                else:
                    break
    else:
        for e in initial_record:
            if e[2]<start_date:
                continue
            else:
                if e[2]<=end_date:
                    att_record.append(e)
                else:
                    break
    return att_record