TIMESTAMP_INIT_YEAR = 2001
TIMESTAMP_INIT = 978307200

class Datetime():

    def timestamp(self, year, month, day, hour, minute, second):
        init_timestamp = TIMESTAMP_INIT
        init_year = TIMESTAMP_INIT_YEAR
        days = 0
        for i in range(year - init_year): 
            y = init_year + i
            if y % 4 == 0:
                days += 366
            else:
                days += 365
                
        print("días: ",days)
        # Sumar dias 
        if year % 4 == 0:
            days_per_month = [31,29,31,30,31,30,31,31,30,31,30,31]
        else:
            days_per_month = [31,28,31,30,31,30,31,31,30,31,30,31]
            
        print("Dias por mes: ", days_per_month)

        for i in range(month-1):
            days += days_per_month[i]

        print(days)

        date_in_seconds = ((day-1) + days) * 24 * 3600
        time_in_seconds = second + minute * 60 + hour * 3600

        timestamp = init_timestamp + date_in_seconds + time_in_seconds


        return timestamp

