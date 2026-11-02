"""workers-service — async work that is not domain state:

* projects domain events into the cross-company activity log
* renders invoice PDFs (fpdf2) on demand
* serves activity-feed reads and admin event statistics
"""

from si_common.service import create_service

from . import consumer, repos
from .routers import router

app = create_service(
    'workers',
    title='StockInvoice workers service',
    binding_keys=('#',),   # every domain event; only activity blocks land here
    consumer=consumer.handle,
    indexes=repos.INDEXES,
    routers=((router, ''),),
)
