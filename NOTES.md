# Preamble
Bash would not be too suitable for this kind of exercise 
(it can be, but it would be overcomplicating the dev's life without any benefit in return).

That leaves following languages:
* Python 3
* Ruby 2.7
* Powershell 7

and neither of those are my primary dev language of choice, so I am going to be using python (the approach might be somewhat naive in some points)

# Assumptions / Considerations
I am going to assume following:
* In case of any error during the migration, that version will be migrated back and the execution will error out without going any further prompting for human intervention to resolve the issue
* I've removed packages like `ruby`  and `powershell` to reduce weight of the image
* removed `MYSQL_PASSWORD` from submission container (we do not need it and it should not be exposed)
* I am assuming that migration files follow this regex mask: `^(\d+)\.?[\w\s]+\.sql$` Eventually it could have been `^(\d+)\.?.*?\.sql$` depending on our use case
* While I've implemented a rollback mechanism, sadly it won't work in case "create table" statement is used due to modus operandi of mysql. Further investigation needed to work around this issue in case of an error.
* I did not change security permissions, at the very least containers should not be running as root
* Although docker-compose contains depends_on, there is still a race condition caused by mysql container coming up too slowly sometimes. It has been dealt with by introducing a small check for socket connectivity, but more elegant approach is needed (happy to discuss)
* Dockerfiles are not efficient, they should be constructed with a single layer
* Migration script should be split further, but I had some weird bug which I had to chase so it ate most of my time 

# Changes to original files
* Added an additional envvar `MYSQL_HOST` to the execution config in docker-compose.yml While it's possible to hardcode the target directly in the script, that would not be the right way to do in my opinion. To improve further, we could specify target port as well, for now I am assuming that it's going to be `3306`
