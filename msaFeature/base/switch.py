from functools import partial

from msaFeature.base.signal import switch_active, switch_checked


class MSASwitch(object):
    """
    A switch encapsulates the concept of an item that is either 'on' or 'off'
    depending on the input.  The switch determines this by checking each of its
    conditions and seeing if it applies to a certain input.  All the switch does
    is ask each of its Conditions if it applies to the provided input.  Normally
    any condition can be true for the MSASwitch to be enabled for a particular
    input, but of ``switch.interlinked`` is set to True, then **all** of the
    switches conditions need to be true in order to be enabled.
    See the Condition class for more information on what a Condition is and how
    it checks to see if it's satisfied by an input.

    Switches can be in 3 core states:
        ``PERMANENT``, ``DISABLED`` and ``CONDITIONAL``.

    In the ``PERMANENT`` state, the MSASwitch is enabled for every input no conditions will be checked.
    ``DISABLED`` MSASwitch's are disabled for any input, no further checks.
    ``CONDITIONAL`` MSASwitch's are only enabled based on their conditions.
    """

    class states:
        DISABLED = 1
        CONDITIONAL = 2
        PERMANENT = 3

    def __init__(
        self,
        name,
        state=states.DISABLED,
        interlinked=False,
        parent=None,
        concent=True,
        manager=None,
        label=None,
        description=None,
        **kwargs
    ):
        self.__init_vars = None
        self._name = str(name)
        self.label = label
        self.description = description
        self.state = state
        self.conditions = []
        self.interlinked = interlinked
        self.parent = parent
        self.concent = concent
        self.children = []
        self.manager = manager
        self.reset()

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        separator = getattr(self.manager, "key_separator", ":")
        parent = self.name.rsplit(separator, 1)[0]
        return parent if parent != self.name else None

    def get_parent(self):
        return self.manager.switch(self.parent) if self.parent else None

    def __repr__(self):
        kwargs = dict(
            state=self.state, interlinked=self.interlinked, concent=self.concent
        )
        parts = ["%s=%s" % (k, v) for k, v in kwargs.items()]
        return '<MSASwitch("%s") conditions=%s, %s>' % (
            self.name,
            len(self.conditions),
            ", ".join(parts),
        )

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.state is other.state
            and self.interlinked is other.interlinked
            and self.concent is other.concent
        )

    def enabled_for(self, inpt):
        """
        Checks to see if this switch is enabled for the provided input.
        If ``compounded``, all switch conditions must be ``True`` for the swtich
        to be enabled.  Otherwise, *any* condition needs to be ``True`` for the
        switch to be enabled.
        The switch state is then checked to see if it is ``GLOBAL`` or
        ``DISABLED``.  If it is not, then the switch is ``SELECTIVE`` and each
        condition is checked.
        Keyword Arguments:
        inpt -- An instance of the ``Input`` class.
        """
        switch_checked.call(self)
        signal_decorated = partial(self.__signal_and_return, inpt)

        if self.state is self.states.PERMANENT:
            return signal_decorated(True)
        elif self.state is self.states.DISABLED:
            return signal_decorated(False)

        result = self.__enabled_func(cond.call(inpt) for cond in self.conditions)
        return signal_decorated(result)

    def save(self):
        """
        Saves this switch in its manager (if present).
        Equivilant to ``self.manager.update(self)``.  If no ``manager`` is set
        for the switch, this method is a no-op.
        """
        if self.manager:
            self.manager.update(self)

    @property
    def changes(self):
        """
        A dicitonary of changes to the switch since last saved.
        Switch changes are a dict in the following format::
            {
                'property_name': {'previous': value, 'current': value}
            }
        For example, if the switch name change from ``foo`` to ``bar``, the
        changes dict will be in the following structure::
            {
                'name': {'previous': 'foo', 'current': 'bar'}
            }
        """
        return dict(list(self.__changes()))

    @property
    def changed(self):
        """
        Boolean of if the switch has changed since last saved.
        """
        return bool(list(self.__changes()))

    def reset(self):
        """
        Resets switch change tracking.
        No switch properties are alterted, only the tracking of what has changed
        is reset.
        """
        self.__init_vars = vars(self).copy()

    @property
    def state_string(self):
        state_vars = vars(self.states)
        rev = dict(zip(state_vars.values(), state_vars))
        return rev[self.state]

    @property
    def __enabled_func(self):
        if self.interlinked:
            return all
        else:
            return any

    def __changes(self):
        for key, value in self.__init_vars.items():
            if key is "_Switch__init_vars":
                continue
            elif key not in vars(self) or getattr(self, key) != value:
                yield (key, dict(previous=value, current=getattr(self, key)))

    def __signal_and_return(self, inpt, is_enabled):
        if is_enabled:
            switch_active.call(self, inpt)

        return is_enabled

    @parent.setter
    def parent(self, value):
        self._parent = value
