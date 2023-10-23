class config:
    class irc:
        server = 'irc.supernets.org'
        port = 6697
        username = 'vortex'
        realname = 'FightBot by vorteckz'
        nickname = 'FightBot'
        channel = '#dev'
        channelkey = 'test'
        password = None
        ssl = True
        v6 = 2
        vhost = None
        admins = {'vortex', 'vorteckz','acidvegas','peanuter'}
    class throttle:
        cmd       = 0.5
        msg       = 0.5
        reconnect = 10
        rejoin    = 3
        last      = 0
        slow      = False
        lastnick  = None