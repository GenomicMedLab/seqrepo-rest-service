import biocommons.seqrepo
import bioutils

from seqrepo_rest_service import __version__
from seqrepo_rest_service.threadglobals import get_seqrepo


def get():
    """Return refget capabilities and dependency information.

    :return: JSON-compatible service information.
    """
    sr = get_seqrepo()

    return {
        "service": {
            "algorithms": ["md5", "trunc512"],
            "circular_supported": False,
            "subsequence_limit": None,
            "supported_api_versions": ["1.0"],
        },
        "x-config": {
            "seqrepo-rest-service": {
                "version": __version__,
                "url": "https://github.com/biocommons/seqrepo-rest-service/",
            },
            "seqrepo": {
                "version": biocommons.seqrepo.__version__,
                "root": str(sr._root_dir),
                "url": "https://github.com/biocommons/biocommons.seqrepo/",
            },
            "bioutils": {
                "version": bioutils.__version__,
                "url": "https://github.com/biocommons/bioutils/",
            },
        },
    }
