# OiRA Statistics

Welcome to the OiRA statistics!

Here are a few hints and explanations to help you find what you're looking for.

## Getting Started

For the best experience with the statistics we recommend to view them in Chrome or
Safari. There have been reports of display issues when using Firefox.

### The Home Screen

After logging in you see the home screen.

If you get lost at any time, you can click the logo (“M”) in the top left corner to
return here.

![Metabase logo](/statistics/images/metabase_logo.png)

You can also use the “Back”/“Forward” buttons of your browser to navigate. The home
screen consists of the “-> Start here” dashboard and your country collection.

### Collections, Dashboards, Cards, Questions

You can think of collections like folders that contain statistics items. Each country
has its own collection. Click your country collection to view its contents.

At the top of the list in your country collection you will find the available dashboards
(yellow icons).

![Dashboard listing](/statistics/images/dashboard_listing.png)

Individual questions are listed below. Dashboards group a set of questions together.
Clicking a dashboard allows you to view all its questions on one screen. It is
recommended to first navigate to a dashboard to get an overview instead of directly
picking a question, unless you already know the exact title of the question you want.
Click the Assessments Dashboard now.

Most dashboards hold a general card with descriptive text about the dashboard. The rest
of the cards on each dashboard show one question.

![Assessments dashboard](/statistics/images/assessments_dashboard.png)

A question displays an aspect of the statistical data. It can take the form of a graph
or chart, a table, or just a number. On the dashboard, usually you can click the title
of a question card to expand the question to its full view. This allows you to examine
it in more detail. Click the title of the card “Accumulated Assessments Over Time”.

This question shows how the number of assessments in your country has developed over
time. Each bar represents the number of assessments that were started up until a
particular time (the end of a certain month). Hover over a bar to see the month and the
number of assessments it represents.

![Example question](/statistics/images/example_question.png)

All questions on the Assessments Dashboard deal with the number of assessments in some
way. Other dashboards have a different focus, e.g. the number of users who have made
assessments.

### Switching Between Table and Chart

In the full view of the question, at the bottom centre of the screen, there are two
buttons representing a table and a graph. Click the table to switch to a tabular
representation of the question, and the graph to switch back to the bar chart.

![Switch between table and chart](/statistics/images/switch_table_graph.png)

### Downloading Data

When viewing a question there is an icon at the bottom right (a cloud with an arrow
pointing down) that allows downloading the data that is currently displayed.

![Download icon](/statistics/images/download_icon.png)

The displayed data can be either the original question that you found on a dashboard or
a modified one that is the result of applying an extra filter (see below). Anything that
is hidden in the current chart or table will also not be present in the downloaded data.

You can choose between comma separated values (csv), an Excel sheet (xlsx) or JavaScript
Object Notation (json) for your download. Both csv and xlsx downloads can be viewed in
Excel.

![Download formats](/statistics/images/download_formats.png)

### Zooming In

Still in the full view of the question, hover the mouse cursor over a data point, in
this case one of the bars in the bar chart (it could also be e.g. a segment in a pie
chart). A tooltip will show more information (i.e. the exact number of assessments that
were started and what time range they were started in, see above).

In the blank area above the bars the mouse cursor will turn to a cross. Click and drag
here to select a time range that you are especially interested in. The view will zoom in
to the range you selected and hide the rest of the data. Alternatively you can use the
two select boxes below the chart (above the table/chart switches) to choose a date range
and a granularity (month, week, quarter etc.).

![Select date/time range](/statistics/images/select_time_range.png)

**Important:** This functionality allows zooming in on the data, not on the chart. This
makes a difference especially when you have accumulated data over time like in
*Accumulated Assessments Over Time*. When zooming in to a date range starting in January
2015, for example, the new chart only takes assessments into account that were started
after that date. It does not accumulate the assessments that were started before 2015
but starts at 0, so that the first bar will only count the assessments started **in**
January 2015 rather than **until** January 2015.

When zoomed in you will see the phrase “Started from *Accumulated Assessments Over
Time*” next to the page title, which links back to the original question. (Remember that
you can also click “Back” in your browser, or return to the home screen at any time by
clicking the logo in the top left corner.)

![Question with filter active](/statistics/images/filter_active.png)

### Filtering

“Zooming in” is a special case of filtering. Active filters are shown near the top left
(below the phrase “Started from *Accumulated Assessments Over Time*”). When zoomed in
you will see a purple bubble stating that a filter on the “Start Date” has been applied
and what date range the filter limits to (something like “Start date is after January 1,
2022”). Clicking the “x” on the bubble removes this filter.

You can also filter by other criteria than time. Click the “Filter” button at the top
right.

A side bar opens to show the available options.

![Filter button](/statistics/images/filter_button.png)

Choose “Tool Path”, then select one or more of the listed tools and click “Add filter”
at the bottom of the side bar. The view will update to show only assessments started
with the chosen tools. A bubble is shown in the top left that describes the filter
(“Tool Path is ...”). Click the “x” on the bubble to remove the filter. The view updates
again to show the unfiltered data.

**Important:** There currently is a known issue in the statistics software that causes
certain questions to lose some configuration when using the filter side bar. The result
will likely not make sense. When in doubt return to the original question and click the
“Show editor” icon at the top right (next to the “Filter” and “Summarize” buttons).

![Show editor button](/statistics/images/show_editor.png)

If there are two blocks with the heading “Summarize” then this question is affected by
the described issue and you can't use the filter side bar. The metabase developers are
working on resolving this issue but for the moment there is no solution available.

![Question editor](question_editor.png)

## Terminology

-   **Accumulated** - Whenever this term is used, we have summed up numbers from the
    beginning of the current time span to the given date. E.g. when viewing all
    available assessments, “Number of assessments” for March 2020 is the number of
    assessments that have been started in March 2020, while “Accumulated assessments”
    for March 2020 is the number of assessments that have been started between the
    beginning of records and the end of March 2020. By using the filter options you can
    also change this time span to any period you are interested in like a specific year.
    E.g. if you are viewing assessments for 2020 only, then “Accumulated assessments”
    for March 2020 is the number of assessments that have been started between the
    beginning of 2020 and the end of March 2020.
-   **Assessment** - A set of answers, actions and other items related to one particular
    use of a certain OiRA tool. Assessment refers to the different risk assessments a
    user has conducted with a tool. One user can do several risk assessments with the
    same or different tools.
-   **Card** - The representation of a question on a dashboard.
-   **Collection** - You can think of collections like folders that contain dashboards,
    questions and other statistics items. Normally each country is represented by one
    collection.
-   **Converted User / Converted Account** - A user who started as a guest and
    subsequently registered an account from within a guest assessment / test session.
-   **Dashboard** - Dashboards allow viewing a set of questions together. Each question
    is displayed as a card on the dashboard.
-   **Guest Assessment** - An assessment started as a guest user.
-   **Guest User** - A temporary user who has started an assessment without first
    registering a full user account. Please note: due to many automated requests the
    guest user count does not actually reflect real people going to the tools before May
    2021, when a feature went live to prevent these machine generated guest assessments.
-   **Question** - A question shows an aspect of the statistical data. The term refers
    to a query, the results of that query, and the visualization and formatting of those
    results (which could be a line graph, a pie chart or just a table of results).
    questions can be displayed as cards on dashboards.
-   **Registered User** - A user who has an account in OiRA. This includes *converted
    users* and users who registered from the start, without first starting an assessment
    as a guest. It does not include guest users who have not been converted.
-   **Test Session** - Synonymous with “Guest assessment”.
-   **Test User** - Synonymous with “Guest user”.
-   **Top Assessment** - An assessment in which more than 70% of risks have been
    answered.
