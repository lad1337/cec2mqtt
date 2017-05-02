from pkg_resources import get_distribution


def version():
    return get_distribution('cec2mqtt').version


__version__ = version()
