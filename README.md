Prior work
https://github.com/kevinharvey/django-tourney
https://github.com/psgoral/Django-Tournament-Creator

Useful libraries
https://www.aropupu.fi/bracket/
    Probably not worth hacking to handle 3 or more teams for a single match
    HTML / CSS it generates can be used as a model
https://www.aropupu.fi/group/

https://htmx.org/
    For live updates


Questions
Do we need to handle / show penalties?

Scenarios (in order of rank ABCD...)
max4adv1
    ACE
        AB
    BDF
    Instead of
    ACEF
        AB
    BD (this group has an unfair advantage)
max4adv2
    ACEG
        ACB
    BDF
    Or maybe rather
    ACEG
        ACBD
    BDF
    Both are valid: the organizer could want either (how to let them choose?)


Version 1:

- Only handle 1v1 single-elimination tournament
- Create Schools and Teams through the Django admin interface

- Setup a tournament:
  -  Enter number of teams (force it to be a power of two: no bye's)
  -  Add teams: the order you add them determines the seeding
  -  Generate matches

- Run a tournament:
    - Visually show the bracket (with jQuery Bracket-like visualization)
    - Judge (only) clicking on a match -> score entering page (could be admin for the Match initially)
    - Judge (only) enters who advanced for the Match
    - Viewers refresh bracket (manually) to show who advanced
    
Version 2:
- Use HTMX to poll to refresh the bracket like in [this video](https://www.youtube.com/watch?v=QsGZ9361hlU)
- Localization?
