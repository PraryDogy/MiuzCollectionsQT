from cfg import JsonData

JsonData.init()

filter_values_ = list(
            i.get("value")
            for i in (*JsonData.dynamic_filters, JsonData.static_filter)
            )

print(filter_values_)