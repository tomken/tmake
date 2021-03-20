#import "HelloAppAppDelegate.h"

#import "HelloIOS.h"

@implementation HelloAppAppDelegate

@synthesize window;

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
//    self.window.backgroundColor = UIColor.whiteColor;
    
    HelloIOS* controller = [[HelloIOS alloc] init];
    self.window.rootViewController = controller;
    [self.window makeKeyAndVisible];
    return TRUE;
}

- (void)dealloc{
	[window release];
	[super dealloc];
}

@end
