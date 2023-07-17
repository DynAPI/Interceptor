# Interceptor
middleman between the clients and your backend to add security or other verifications to the requests

![THE INTERCEPTOR](assets/logo.png)

## How a request normally works

The client sends a request to the backend. Either there is no authentication or the backend(-infrastructure) has to be extended which is not always possible.

[![](https://mermaid.ink/img/pako:eNo1jr0OwjAMhF8l8lxgz9CBHzExwZjFSgyNSByaOhKo6rsTCNxk3Z1P3ww2OQINE42F2NLe4y1jNKyqdsETy6rvt2jvxE6r4-GiNi38eTVtNa08O3quB4nBMHQQKUf0ro7Pnw8DMlAkA7qeTEUyBgOGl1rFIun8YgtacqEOysOh_FlAXzFM1SXnJeVTA_5yL2_cUEA7?type=png)](https://mermaid.live/edit#pako:eNo1jr0OwjAMhF8l8lxgz9CBHzExwZjFSgyNSByaOhKo6rsTCNxk3Z1P3ww2OQINE42F2NLe4y1jNKyqdsETy6rvt2jvxE6r4-GiNi38eTVtNa08O3quB4nBMHQQKUf0ro7Pnw8DMlAkA7qeTEUyBgOGl1rFIun8YgtacqEOysOh_FlAXzFM1SXnJeVTA_5yL2_cUEA7)

## How a request with Interceptor works

The client sends a request to the backend (Interceptor) which does the authentication.
If the request is verified it's let through to the real backend.

[![](https://mermaid.ink/img/pako:eNqFUU1LQzEQ_Cthr239AE9BHlgr4sFeVKiQy5qsfdFk88zboLb0v5v6KrQguqdlmNnZnV2DTY5AQ09vhdjSzOMyYzSsal0GTyyTphndsFC21EnKWl1f3avjgbGHV9pkEGh1dnKqHhiLtCn7Fbn_x6nzp9yoi50CxSfWaoq9t8ot5sG-dO-Pi_nqN9fRFO0rsTtYbIdtlzow8-zo46iVGP48YJ8GY4iUI3pXc1pvZQakpUgGdG2ZimQMBgxvKrUene4-2YKWXGgMpXMoP7GCfsbQV5Scr463Q_bfL9h8AbuKhJ0?type=png)](https://mermaid.live/edit#pako:eNqFUU1LQzEQ_Cthr239AE9BHlgr4sFeVKiQy5qsfdFk88zboLb0v5v6KrQguqdlmNnZnV2DTY5AQ09vhdjSzOMyYzSsal0GTyyTphndsFC21EnKWl1f3avjgbGHV9pkEGh1dnKqHhiLtCn7Fbn_x6nzp9yoi50CxSfWaoq9t8ot5sG-dO-Pi_nqN9fRFO0rsTtYbIdtlzow8-zo46iVGP48YJ8GY4iUI3pXc1pvZQakpUgGdG2ZimQMBgxvKrUene4-2YKWXGgMpXMoP7GCfsbQV5Scr463Q_bfL9h8AbuKhJ0)
