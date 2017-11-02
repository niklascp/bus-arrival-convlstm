set datefirst 1;

with
[LinkTravelTime] as
(
    select
        -- Metadata
        [JourneyLinkRef] = p.[JourneyPointRef],
        j.[JourneyRef],
        p.[SequenceNumber],
        [DateTime] = isnull([ObservedDepartureDateTime], [PlannedDepartureDateTime]),
        jp.[LineDirectionCode], 
        [LineDirectionLinkOrder] = dense_rank() over (partition by jp.[LineDirectionCode] order by sec.[LineDirectionLegacyOrder]) - 1,
        [LinkRef] = concat(sec.StopPointSectionFromNumber, ':', sec.StopPointSectionToNumber),
        [LinkName] = concat(sec.[StopPointSectionFromName], ' - ', sec.[StopPointSectionToName]),
        --
	    [DayOfWeek] = case 
		    when j.OperatingDayType = 1 then datepart(WEEKDAY, cast(p.[PlannedArrivalDateTime] as date)) 
		    when j.OperatingDayType = 2 then 6
		    when j.OperatingDayType = 3 then 7
	    end,
               
        [LinkTravelTime] = datediff(second, lag(p.[ObservedDepartureDateTime]) over (partition by j.[JourneyRef] order by p.[JourneyPointRef]), p.[ObservedArrivalDateTime])
    FROM
        [data].[RT_Journey] j
        join [dim].[JourneyPattern] jp on jp.[JourneyPatternId] =  j.[JourneyPatternId] and jp.[IsCurrent] = 1
        join [data].[RT_JourneyPoint] p on p.[JourneyRef] = j.[JourneyRef]
        join [dim].[JourneyPatternSection] sec on sec.JourneyPatternId = jp.[JourneyPatternId] and sec.SequenceNumber = p.SequenceNumber and sec.IsCurrent = 1
    where
        --j.[LineDesignation] = '4A'
        j.[JourneyPatternId] in (
        1310000118937825,
        1310000067545315,
        1310000117010308,
        1310000118937760,
        1310000088441711)
        and j.[OperatingDayDate] between '2017-10-10' and '2017-10-14'
        and p.[IsStopPoint] = 1
)
select -- 692 276
    [JourneyLinkRef],
    [JourneyRef],    
    [DateTime],
    [LineDirectionCode],
    [LineDirectionLinkOrder],
    [LinkRef],
    [LinkName],

    [DayOfWeek],

    [LinkTravelTime] = case when [LinkTravelTime] > 0 then [LinkTravelTime] end
from
    [LinkTravelTime]
where
    [SequenceNumber] > 1
order by
    [JourneyLinkRef]