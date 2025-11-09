import React from 'react';
import data from "../../app/data/data.json"
import { AppSidebar } from "@/components/app-sidebar"
import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { DataTable } from "@/components/data-table"
import { SectionCards } from "@/components/section-cards"
import { SiteHeader } from "@/components/site-header"
import {
    SidebarInset,
    SidebarProvider,
} from "@/components/ui/sidebar"
import { Header } from '@/components/Layouts/Headers';
import { NavItem } from '@/components/Layouts/NavItem';
import { ThemeSwitch } from '@/components/theme-switch';
import { ProfileDropdown } from '@/components/profile-dropdown';
import { ConfigDrawer } from '@/components/config-drawer';

const navItem = [
    {
        title: 'Overview',
        href: 'overview',
        isActive: true,
        disabled: false,
    },
    {
        title: 'Customers',
        href: 'customers',
        isActive: false,
        disabled: true,
    },
    {
        title: 'Products',
        href: 'products',
        isActive: false,
        disabled: true,
    },
    {
        title: 'Settings',
        href: 'settings',
        isActive: false,
        disabled: true,
    },
]

const Dashboard = () => {
    return (
        <SidebarProvider
            style={
                {
                    "--sidebar-width": "calc(var(--spacing) * 72)",
                    "--header-height": "calc(var(--spacing) * 12)",
                }
            }
        >
            <AppSidebar variant="inset" />
            <SidebarInset>
                {/* <SiteHeader /> */}
                <Header>
                    <NavItem links={navItem} />
                    <div className='ms-auto flex items-center space-x-4'>
                        <ThemeSwitch />
                        <ConfigDrawer/>
                        <ProfileDropdown />
                    </div>
                </Header>
                <div className="flex flex-1 flex-col">
                    <div className="@container/main flex flex-1 flex-col gap-2">
                        <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                            <SectionCards />
                            <div className="px-4 lg:px-6">
                                <ChartAreaInteractive />
                            </div>
                            <DataTable data={data} />
                        </div>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
};

export default Dashboard;